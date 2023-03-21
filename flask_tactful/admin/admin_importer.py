import csv
import codecs
import datetime
import json
from sqlalchemy.inspection import inspect
from flask import flash, redirect, request
from flask_admin import expose
from flask_admin.babel import gettext
from flask_admin.helpers import get_redirect_target
from flask_admin.contrib.sqla import ModelView


class AdminImporter(ModelView):
    """Allows Flask Admin views to import CSV,JSON data into the database model
    If you inherit your Admin ModelView from this class, it will automatically support an "/import/" action
    This import action will automatically import and parse a CSV file with column names matching the model 
    You can export any Admin model, in order to see the column names format 


    Args:
        ModelView (FlaskAdminModel): Flask Admin Model view 

    """

    can_import = True
    """ Enable import for this model, can be overidden in your AdminModelView class """
    import_types = ['csv']
    """ currently supports CSV only, but will be extended to support JSON """

    list_template = 'admin/templates/custom_list.html'

    @expose('/import/<import_type>/', methods=['POST'])
    def import_file(self, import_type):
        return_url = get_redirect_target() or self.get_url('.index_view')

        if not self.can_import or (import_type not in self.import_types):
            flash(gettext('Permission denied.'), 'error')
            return redirect(return_url)

        flask_file = request.files['file']
        if not flask_file:
            flash(gettext('Please Upload a file'), 'error')
            return redirect(return_url)

        if import_type == 'csv':
            return self._import_csv(return_url, flask_file)
        else:
            flash(gettext('Format not supported yet'), 'error')
            return redirect(return_url)

    def _get_column_names_dict(self):
        """ returns dict with { PrettyName: model_name } """
        name_tuples = self.get_export_columns()
        return {nt[1]: nt[0] for nt in name_tuples}

    def _convert_value(self, val, val_type=None):
        # also parse the value "False" should be Boolean not string

        # Interpret the string as a Python literal
        # return literal_eval(val)
        print("parsing >> ", val_type, val)
        if val:
            if val_type is str:
                return val
            elif val_type is dict:
                print("json >> ", val, type(val))
                try:
                    return json.loads(val)
                except json.decoder.JSONDecodeError:
                    # valid json is double-quoted, but sometimes objects are single quoted, fix
                    fixed_json = val.replace("'", '"')
                    return json.loads(fixed_json)

            elif val_type is datetime.datetime:
                try:
                    return datetime.datetime.strptime(val, "%Y-%m-%d %H:%M:%S.%f")  # iso format
                except ValueError:
                    return datetime.datetime.strptime(val, "%Y-%m-%d %H:%M:%S")  # iso format
            elif val_type is datetime.date:
                try:
                    return datetime.datetime.strptime(val, "%Y-%m-%d").date()  # iso format
                except ValueError:
                    return None
            elif val_type is bool:
                return not val == 'False'
            else:
                return val_type(val)
        else:
            return None

    def load_relations(self, row, mapper):
        relations = mapper.relationships
        # copy where we will replace columns with the related objects
        expanded_row = row.copy()
        # foreach relationship column in our model
        for (colname, relation) in relations.items():
            print("relation", colname, relation, row)
            related_instances = []
            related_model = relation.mapper.entity

            # value for the related item (usually Name of that related item (Profile Name or Branch Name))
            # some relations are one-to-many and some are one-to-one, so decode accordingly
            values = row.get(colname)
            if relation.uselist and values:
                values = values.split(',')
            else:
                values = [values]

            # if entity relation has not values, skip it
            if colname in row and values:
                if not hasattr(related_model, "__unique__"):
                    raise Exception("cannot detect unique column, declare __unique__ = ['column_name1', 'column_name2'] in your model {0}".format(related_model))
                unique_col_names = related_model.__unique__

                related_query = self.session.query(related_model)
                # if model is profile based
                if hasattr(related_model, "profile") and row.get("profile"):
                    profile_col = getattr(related_model, "profile")
                    related_query = related_query.filter(profile_col.has(name=row.get("profile")))

                for value in values:
                    filtered_query = related_query
                    for unqiue_col_name in unique_col_names:
                        query_value = value
                        col_type = getattr(related_model, unqiue_col_name).type.python_type
                        if col_type is int:
                            query_value = int(value) if value != '' else 0
                        unique_col = getattr(related_model, unqiue_col_name)
                        filtered_query = filtered_query.filter(unique_col == query_value)
                    related_instance = filtered_query.one_or_none()
                    if not related_instance and value != '':
                        raise Exception(f"value {value} not found  in {related_model}")
                    elif related_instance:
                        related_instances.append(related_instance)
                if len(related_instances) == 0:
                    expanded_row.pop(colname)
                else:
                    expanded_row[colname] = related_instances if relation.uselist else related_instances[0]

        return expanded_row

    def convert_columns(self, row, mapper):
        for column in mapper.columns:
            col_type = column.type.python_type
            print("column", column.name, col_type)
            if column.name in row:
                row[column.name] = self._convert_value(row[column.name], col_type)

    def uglify_column_names(self, row):
        row_names = self._get_column_names_dict()
        # translate pretty names to python names Profile Name == profile_name
        return {row_names.get(col[0], col[0]): col[1] for col in row.items()}

    def read_csv(self, csv_file):
        """ reads a csv file into an list of dicts that represent each row """
        rows = []
        # pylint: disable=broad-except
        try:
            stream = codecs.iterdecode(csv_file.stream, 'utf-8')
            for row in csv.DictReader(stream, dialect=csv.excel):
                if row:
                    rows.append(row)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to read csv rows. %(error)s', error=str(ex)), 'error')
            return []

        return rows

    # Checks Model.__unique__ array for unique columns and searches the table for them
    # and if it finds them returns the instance so we can update it with the CSV values
    def get_unique_if_exists(self, row):
        original_instance = None
        has_unique = False
        # overwrite existing items, find these items is the __unique_ columns already exist
        if hasattr(self.model, "__unique__") and self.model.__unique__:
            unique_col_names = self.model.__unique__    # always an array
            unique_cols = [(col_name, getattr(self.model, col_name)) for col_name in unique_col_names]
            original_query = self.session.query(self.model)
            # if model is profile based
            if hasattr(self.model, "profile") and row.get("profile"):
                profile_col = getattr(self.model, "profile")
                original_query = original_query.filter(profile_col.has(name=row.get("profile")))

            for (unique_col_name, unique_col) in unique_cols:
                if unique_col_name in row and row.get(unique_col_name):
                    original_query = original_query.filter(unique_col == row.get(unique_col_name))
                    has_unique = True
            # raise an exception if we found more than one row that match the query
            # this means that the query is poorly constructed or not really unique
            if has_unique:
                original_instance = original_query.one_or_none()
        return original_instance

    def _import_csv(self, return_url, csv_file):
        """
            Import a CSV file into database
            it handles the following:
                - type conversion from csv string, into the correct model type including Boolean
                - Relationship loading using names (not IDs), so it can be moved around between databases
                - Handles Human readable pretty names and converts them to the Model/DB names
                - Rollsback on errors
                - Helpful error messages 
                - if a column is marked as __unique__ accross a relationship, it checks for its existance then updates it
        """
        rows = self.read_csv(csv_file)

        mapper = inspect(self.model)
        # pylint: disable=broad-except
        entries = []
        try:
            for row in rows:
                if row:
                    row = self.uglify_column_names(row)

                    # converts strings loaded from csv to column types
                    self.convert_columns(row, mapper)
                    # load the relations for foreign keys
                    original_instance = self.get_unique_if_exists(row)
                    # check if this row exists before?

                    row = self.load_relations(row, mapper)

                    # if it already exists, update it, else add new
                    is_created = True
                    if not original_instance:
                        original_instance = self.model()
                        is_created = False

                    self.model_from_dict(original_instance, **row)
                    self.session.add(original_instance)
                    entries.append((row, original_instance, is_created))

            self.session.commit()
            for (row, model, is_created) in entries:
                self.on_model_change(row, model, is_created)
            flash("{0} rows imported successfully!".format(len(rows)))
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to import csv rows. %(error)s', error=str(ex)), 'error')
            self.session.rollback()

        return redirect(return_url)

    # loads model data from input dict, does not handle related items
    # it is better than model.__init__() because it ignores non existing keys while init crashes if a non existing item is sent

    def model_from_dict(self, model, **kwargs):
        for key, value in kwargs.items():
            if hasattr(model, key):
                # print("setting {0}= {1}".format(key, value))
                setattr(model, key, value)
            else:
                print("NOT setting {0} not found (value={1})".format(key, value))
