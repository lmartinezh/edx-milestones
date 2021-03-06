# pylint: disable=no-member
"""
Application data management/abstraction layer.  Responsible for:

1) Accessing information from various resources:
* Internal application state  (through local models in models.py)
* External application state  (ORM bindings with other apps, yuck)
* Remote data services (through service adapters in resources.py)

2) Calculating derivative information from existing state:
* Algorithms and data manipulations
* Aggregations
* Annotations
* Alternative data representations

Accepts and returns standard Python data structures (dicts, arrays of dicts)
for easy consumption and manipulation by callers -- the queryset stops here!

Note the terminology difference at this layer vs. API -- create/fetch/update/delete/

When the time comes for remote resources, import the module like so:
if getattr(settings, 'TEST_MODE', False) or os.getenv('TRAVIS_MODE', False):
    import milestones.tests.mocks.resources as remote
else:
    import milestones.resources as remote
"""
from . import exceptions
from . import models as internal
from . import serializers


# PRIVATE/INTERNAL METHODS
def _get_milestone_relationship_type(relationship):
    """
    Retrieves milestone relationship type object from backend
    """
    try:
        return internal.MilestoneRelationshipType.objects.get(
            name=relationship,
            active=True
        )
    except internal.MilestoneRelationshipType.DoesNotExist:
        if relationship in ['requires', 'fulfills']:
            return internal.MilestoneRelationshipType.objects.create(
                name=relationship,
                active=True
            )
        else:
            raise exceptions.InvalidMilestoneRelationshipTypeException()


# PUBLIC METHODS
def create_milestone(milestone):
    """
    Inserts a new milestone into app/local state
    Returns a dictionary representation of the object
    """
    milestone_obj = serializers.deserialize_milestone(milestone)
    milestone, __ = internal.Milestone.objects.get_or_create(  # pylint: disable=invalid-name
        namespace=milestone_obj.namespace,
        name=milestone_obj.name,
        active=True,
        defaults={
            'description': milestone_obj.description,
        }
    )
    return serializers.serialize_milestone(milestone)


def update_milestone(milestone):
    """
    Updates an existing milestone in app/local state
    Returns a dictionary representation of the object
    """
    milestone_obj = serializers.deserialize_milestone(milestone)
    try:
        milestone = internal.Milestone.objects.get(id=milestone_obj.id)
        milestone.name = milestone_obj.name
        milestone.namespace = milestone_obj.namespace
        milestone.description = milestone_obj.description
        milestone.active = milestone_obj.active
    except internal.Milestone.DoesNotExist:
        raise exceptions.InvalidMilestoneException()
    return serializers.serialize_milestone(milestone)


def delete_milestone(milestone):
    """
    Deletes an existing milestone from app/local state
    No return currently defined for this operation
    """
    milestone_obj = serializers.deserialize_milestone(milestone)
    _delete_milestone(milestone_obj)


def _delete_milestone(milestone):
    """
    Internal helper for milestone removals -- also removes defined dependencies
    """
    # Remove related entities, and then remove the Milestone
    internal.CourseMilestone.objects.filter(
        milestone=milestone.id).delete()
    internal.CourseContentMilestone.objects.filter(
        milestone=milestone.id).delete()
    internal.UserMilestone.objects.filter(
        milestone=milestone.id).delete()
    internal.Milestone.objects.filter(
        id=milestone.id).delete()


def fetch_milestones(milestone):
    """
    Retrieves a set of matching milestones from app/local state
    Returns a list-of-dicts representation of the object
    """
    if milestone is None:
        raise exceptions.InvalidMilestoneException()
    milestone_obj = serializers.deserialize_milestone(milestone)
    if milestone_obj.id is not None:
        return serializers.serialize_milestones(internal.Milestone.objects.filter(
            id=milestone_obj.id,
            active=True,
        ))
    if milestone_obj.namespace is not None:
        return serializers.serialize_milestones(internal.Milestone.objects.filter(
            namespace=milestone_obj.namespace,
            active=True
        ))
    return []


def create_course_milestone(course_key, relationship, milestone):
    """
    Inserts a new course-milestone into app/local state
    No response currently defined for this operation
    """
    relationship_type = _get_milestone_relationship_type(relationship)
    milestone_obj = serializers.deserialize_milestone(milestone)
    internal.CourseMilestone.objects.get_or_create(
        course_id=unicode(course_key),
        milestone=milestone_obj,
        milestone_relationship_type=relationship_type,
        active=True,
    )


def delete_course_milestone(course_key, milestone):
    """
    Removes an existing course-milestone from app/local state
    No response currently defined for this operation
    """
    try:
        internal.CourseMilestone.objects.get(
            course_id=unicode(course_key),
            milestone=milestone['id'],
            active=True,
        ).delete()
    except internal.CourseMilestone.DoesNotExist:
        pass


def fetch_courses_milestones(course_keys, relationship=None, user=None):
    """
    Retrieves the set of milestones currently linked to the specified courses
    Optionally pass in 'relationship' (ex. 'fulfills') to filter down the set
    """
    queryset = internal.CourseMilestone.objects.filter(
        course_id__in=course_keys,
        active=True
    ).select_related('milestone')

    # if milestones relationship type found then apply the filter
    if relationship is not None:
        mrt = _get_milestone_relationship_type(relationship)
        queryset = queryset.filter(
            milestone_relationship_type=mrt.id,
        )

    # To pull the list of milestones a user HAS, use get_user_milestones
    # Use fetch_courses_milestones to pull the list of milestones that a user does not yet
    # have for the specified course
    if relationship == 'requires' and user and user.get('id', 0) > 0:
        queryset = queryset.exclude(milestone__usermilestone__user_id=user['id'])

    # Assemble the response container
    course_milestones = []
    if len(queryset):
        for milestone in queryset:
            course_milestones.append(serializers.serialize_milestone_with_course(milestone))

    return course_milestones


def create_course_content_milestone(course_key, content_key, relationship, milestone):
    """
    Inserts a new course-content-milestone into app/local state
    No response currently defined for this operation
    """
    relationship_type = _get_milestone_relationship_type(relationship)
    milestone_obj = serializers.deserialize_milestone(milestone)
    internal.CourseContentMilestone.objects.get_or_create(
        course_id=unicode(course_key),
        content_id=unicode(content_key),
        milestone=milestone_obj,
        milestone_relationship_type=relationship_type,
        active=True,
    )


def delete_course_content_milestone(course_key, content_key, milestone):
    """
    Removes an existing course-content-milestone from app/local state
    No response currently defined for this operation
    """
    try:
        internal.CourseContentMilestone.objects.get(
            course_id=unicode(course_key),
            content_id=unicode(content_key),
            milestone=milestone['id'],
            active=True,
        ).delete()
    except internal.CourseContentMilestone.DoesNotExist:
        pass


def fetch_course_content_milestones(course_key, content_key, relationship=None):
    """
    Retrieves the set of milestones currently linked to the specified course content
    Optionally pass in 'relationship' (ex. 'fulfills') to filter down the set
    Optionally pass in 'user' to further-filter the set (ex. for retrieving unfulfilled milestones)
    """
    queryset = internal.Milestone.objects.filter(active=True)

    if course_key:
        queryset = queryset.filter(coursecontentmilestone__course_id=unicode(course_key))

    if content_key:
        queryset = queryset.filter(coursecontentmilestone__content_id=unicode(content_key))

    if relationship:
        mrt = _get_milestone_relationship_type(relationship)
        queryset = internal.Milestone.objects.filter(
            coursecontentmilestone__milestone_relationship_type=mrt.id,
            active=True,
        )

    course_content_milestones = []
    if len(queryset):
        for milestone in queryset:
            course_content_milestones.append(serializers.serialize_milestone(milestone))

    return course_content_milestones


def fetch_milestone_courses(milestone, relationship=None):
    """
    Retrieves the set of courses currently linked to the specified milestone
    Optionally pass in 'relationship' (ex. 'fulfills') to filter down the set
    """
    milestone_obj = serializers.deserialize_milestone(milestone)
    queryset = internal.CourseMilestone.objects.filter(
        milestone=milestone_obj,
        active=True
    ).select_related('milestone')

    # if milestones relationship type found then apply the filter
    if relationship is not None:
        mrt = _get_milestone_relationship_type(relationship)
        queryset = queryset.filter(
            milestone_relationship_type=mrt.id,
        )

    # Assemble the response container
    milestone_courses = []
    if len(queryset):
        for milestone in queryset:
            milestone_courses.append(serializers.serialize_milestone_with_course(milestone))

    return milestone_courses


def fetch_milestone_course_content(milestone, relationship=None):
    """
    Retrieves the set of course content modules currently linked to the specified milestone
    Optionally pass in 'relationship' (ex. 'fulfills') to filter down the set
    """
    milestone_obj = serializers.deserialize_milestone(milestone)
    queryset = internal.CourseContentMilestone.objects.filter(
        milestone=milestone_obj,
        active=True
    ).select_related('milestone')

    # if milestones relationship type found then apply the filter
    if relationship is not None:
        mrt = _get_milestone_relationship_type(relationship)
        queryset = queryset.filter(
            milestone_relationship_type=mrt.id,
        )

    # Assemble the response container
    milestone_course_content = []
    for milestone in queryset:
        milestone_course_content.append(
            serializers.serialize_milestone_with_course_content(milestone)
        )

    return milestone_course_content


def create_user_milestone(user, milestone):
    """
    Inserts a new user-milestone into app/local state
    No response currently defined for this operation
    """
    milestone_obj = serializers.deserialize_milestone(milestone)
    internal.UserMilestone.objects.get_or_create(
        user_id=user['id'],
        milestone=milestone_obj,
        active=True,
    )


def delete_user_milestone(user, milestone):
    """
    Removes an existing user-milestone from app/local state
    No response currently defined for this operation
    """
    try:
        internal.UserMilestone.objects.get(
            user_id=user['id'],
            milestone=milestone['id'],
            active=True,
        ).delete()
    except internal.UserMilestone.DoesNotExist:
        pass


def fetch_user_milestones(user, milestone=None):
    """
    Retrieves the set of milestones currently linked to the specified user
    """
    if milestone is None:
        queryset = internal.Milestone.objects.filter(
            usermilestone__user_id=user['id'],
            active=True,
        )
    else:
        queryset = internal.Milestone.objects.filter(
            id=milestone['id'],
            usermilestone__user_id=user['id'],
            active=True,
        )
    user_milestones = []
    if len(queryset):
        for milestone in queryset:
            user_milestones.append(serializers.serialize_milestone(milestone))
    return user_milestones


def delete_content_references(content_key):
    """
    Removes references to content keys within this app (ref: api.py)
    Supports the 'delete entrance exam' Studio use case, when Milestones is enabled
    """
    internal.CourseContentMilestone.objects.filter(content_id=unicode(content_key)).delete()


def delete_course_references(course_key):
    """
    Removes references to course keys within this app (ref: receivers.py and api.py)
    """
    internal.CourseMilestone.objects.filter(course_id=unicode(course_key)).delete()
    internal.CourseContentMilestone.objects.filter(course_id=unicode(course_key)).delete()
