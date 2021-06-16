from peewee import IntegerField


class EnumField(IntegerField):
    """
    This class enable an Enum like field for Peewee
    """
    def __init__(self, choices, *args, **kwargs):
        super(IntegerField, self).__init__(*args, **kwargs)
        self.choices = choices

    def db_value(self, value):
        return value.value

    def python_value(self, value):
        return self.choices(value)
