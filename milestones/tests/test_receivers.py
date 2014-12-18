from django.conf import settings
from django.dispatch import receiver
from django.test import TestCase

from opaque_keys.edx.keys import CourseKey

from milestones import api

from mocks import signals as mock_signals


class ReceiverTestCase(TestCase):

    def setUp(self):
        """
        Test Case scaffolding
        """
        self.signal_log = []
        self.test_course_key = CourseKey.from_string('the/course/key')
        self.test_prerequisite_course_key = CourseKey.from_string('prerequisite/course/key')
        self.test_milestone_data = {
            'name': 'Test Milestone',
            'namespace': unicode(self.test_prerequisite_course_key),
            'description': 'This is only a test.',
        }

    def test_on_course_deleted(self):
        """
        Note, this test adds a milestone and two course links
        We're going to confirm that all three entities are removed
        """

        # Add a new milestone and links to the system
        milestone = api.add_milestone(milestone=self.test_milestone_data)
        milestones = api.add_course_milestone(course_key=self.test_course_key, relationship='requires', milestone=milestone)
        milestones = api.add_course_milestone(course_key=self.test_prerequisite_course_key, relationship='fulfills', milestone=milestone)

        # Inform the milestones app that the prerequisite course has
        # now been removed from the system.
        mock_signals.course_deleted.send(
            sender=self,
            course_key=self.test_prerequisite_course_key
        )

        # Confirm the milestone and links no longer exist
        milestones = api.get_milestones(namespace=unicode(self.test_prerequisite_course_key))
        self.assertEqual(len(milestones), 0)

        course_milestones = api.get_course_milestones(course_key=self.test_course_key)
        self.assertEqual(len(course_milestones), 0)

        prereq_milestones = api.get_course_milestones(course_key=self.test_prerequisite_course_key)
        self.assertEqual(len(prereq_milestones), 0)
