"""
Application-specific exception classes used throughout the implementation
"""


class InvalidCourseKeyException(Exception):
    """
    CourseKey validation exception class
    """
    pass


class InvalidContentKeyException(Exception):
    """
    Course content/module/usage key validation exception class
    """
    pass


class InvalidMilestoneException(Exception):
    """
    Milestone validation exception class
    """
    pass


class InvalidMilestoneRelationshipTypeException(Exception):
    """
    Milestone Relationship Type validation exception class
    """
    pass


class InvalidUserException(Exception):
    """
    User validation exception class
    """
    pass


def raise_exception(entity_type, entity, exception):
    """ Exception helper """
    raise exception(
        'The {} you have provided is not valid: {}'.format(entity_type, entity)
    )
