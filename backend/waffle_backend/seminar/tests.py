from django.contrib.auth.models import User
from django.test import Client, TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
import json

from seminar.models import Seminar, UserSeminar
from user.models import InstructorProfile, ParticipantProfile
from user.tests_user import GetUserIdTestCase


class PostSeminarTestCase(TestCase):
    client = Client()

    def setUp(self):
        # participant1
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant1",
                "password": "password",
                "first_name": "Marcel",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.participant1_token = 'Token ' + Token.objects.get(user__username='participant1').key

        # instructor1
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "instructor1",
                "password": "password",
                "first_name": "Marcel",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "instructor",
                "company": "waffle",
                "year": 2
            }),
            content_type='application/json'
        )
        self.instructor1_token = 'Token ' + Token.objects.get(user__username='instructor1').key

        # instructor2
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "instructor2",
                "password": "password",
                "first_name": "Marcel",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "instructor",
                "company": "waffle",
                "year": 2
            }),
            content_type='application/json'
        )
        self.instructor2_token = 'Token ' + Token.objects.get(user__username='instructor2').key

        # seminar1
        self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "Archaeology",
                "time": "12:12",
                "online": True,
                "count": 3,
                "capacity": 2,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )

    def test_post_seminar_request(self):
        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "Archaeology",
                "time": "07:08",
                "online": True,
                "capacity": 3,
                "count": 4,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("name", data)
        self.assertIn("time", data)
        self.assertIn("online", data)
        self.assertIn("capacity", data)
        self.assertIn("count", data)
        self.assertIn("participants", data)
        self.assertIn("instructors", data)

        seminars = Seminar.objects.all()
        self.assertEqual(seminars.count(), 2)
        self.assertIsNotNone(data["instructors"], msg="The Instructor must be included in each seminar")

    def test_post_seminar_incomplete_request(self):
        # AnonymousUser
        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "Archaeology",
                "time": "12:12",
                "online": True,
                "count": 3,
                "capacity": 2,
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Instructor can't be charged in more than two seminars.
        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "Archaeology",
                "time": "12:12",
                "online": True,
                "count": 3,
                "capacity": 2,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Only instructor can open the seminar
        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "Archaeology",
                "time": "12:12",
                "online": True,
                "count": 3,
                "capacity": 2,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant1_token
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # No Seminar name
        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "time": "12:12",
                "online": True,
                "count": 3,
                "capacity": 2,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', data)

        # blank seminar name
        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "",
                "time": "12:12",
                "online": True,
                "count": 3,
                "capacity": 2,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('name', data)

        # online is not boolean
        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "FullStack",
                "time": "12:12",
                "online": "1234",
                "count": 3,
                "capacity": 2,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('online', data)

        # count isn't positive-integer
        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "FullStack",
                "online": False,
                "time": "12:12",
                "count": -3,
                "capacity": 2,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('count', data)

        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "FullStack",
                "online": False,
                "time": "12:12",
                "count": 3.8,
                "capacity": 2,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('count', data)

        # capacity isn't positive-integer
        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "FullStack",
                "online": False,
                "time": "12:12",
                "count": 3,
                "capacity": -2,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('capacity', data)

        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "FullStack",
                "online": False,
                "time": "12:12",
                "count": 3,
                "capacity": 2.6,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('capacity', data)

        # time format should be hh:mm
        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "FullStack",
                "online": False,
                "time": "120:12",
                "count": 3,
                "capacity": 6,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('time', data)


class PutSeminarTestCase(TestCase):
    client = Client()

    def setUp(self):
        # instructor 생성
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "instructor_put_1",
                "password": "password",
                "first_name": "Marcel",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "instructor",
                "company": "waffle",
                "year": 2,
            }),
            content_type='application/json'
        )
        self.instructor_token = 'Token ' + Token.objects.get(user__username='instructor_put_1').key

        # participant 생성
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant_put_1",
                "password": "password",
                "first_name": "Marcel",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.participant_token_1 = 'Token ' + Token.objects.get(user__username='participant_put_1').key

        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant_put_2",
                "password": "password",
                "first_name": "Marcel",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.participant_token_2 = 'Token ' + Token.objects.get(user__username='participant_put_2').key

        # seminar 생성
        self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "Art History",
                "time": "12:12",
                "online": True,
                "count": 3,
                "capacity": 1
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor_token
        )

        user_count = User.objects.count()
        participant_count = ParticipantProfile.objects.count()
        instructor_count = InstructorProfile.objects.count()
        seminar_count = Seminar.objects.count()
        self.assertListEqual([user_count, participant_count, instructor_count, seminar_count], [3, 2, 1, 1])

    def test_put_seminar_invalid_request(self):
        participant1 = User.objects.get(username="participant_put_1")
        seminar1 = Seminar.objects.first()
        UserSeminar.objects.create(user=participant1, seminar=seminar1, role="participant")
        # only instructor can update the responsible seminar
        response = self.client.put(
            '/api/v1/seminar/{}/'.format(Seminar.objects.last().id),
            json.dumps({
                "name": "FullStack",
                "time": "12:34",
                "online": False,
                "count": 3,
                "capacity": 1,
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.put(
            '/api/v1/seminar/{}/'.format(Seminar.objects.first().id),
            json.dumps({
                "name": "FullStack",
                "time": "12:34",
                "online": False,
                "count": 3,
                "capacity": 1,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant_token_1
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # No Seminar
        response = self.client.put(
            '/api/v1/seminar/0/',
            json.dumps({
                "name": "Art History",
                "time": "12:12",
                "online": True,
                "count": 3,
                "capacity": 1
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor_token
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # cannot change capacity
        response = self.client.put(
            '/api/v1/seminar/{}/'.format(seminar1.id),
            json.dumps({
                "name": "Art History",
                "time": "12:12",
                "online": True,
                "count": 3,
                "capacity": 0
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # No Seminar name
        response = self.client.put(
            '/api/v1/seminar/{}/'.format(seminar1.id),
            json.dumps({
                "name": "",
                "time": "12:12",
                "online": True,
                "count": 3,
                "capacity": 1
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_seminar_request(self):
        seminar1 = Seminar.objects.first()

        response = self.client.put(
            '/api/v1/seminar/{}/'.format(seminar1.id),
            json.dumps({
                "name": "Art History",
                "time": "12:12",
                "online": True,
                "count": 3,
                "capacity": 3
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GetSeminarIdTestCase(TestCase):
    client = Client()

    def setUp(self):
        # participant1
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant1",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.participant1_token = 'Token ' + Token.objects.get(user__username='participant1').key

        # participant2
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant2",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.participant2_token = 'Token ' + Token.objects.get(user__username='participant2').key

        # instructor1
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "instructor1",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "instructor",
                "company": "orangenongjang",
                "year": 1
            }),
            content_type='application/json'
        )
        self.instructor1_token = 'Token ' + Token.objects.get(user__username='instructor1').key

    def test_get_valid_seminar_id(self):
        # seminar1
        self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "Bayesian",
                "time": "14:30",
                "online": True,
                "count": 3,
                "capacity": 2
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )

        user_count = User.objects.count()
        participant_count = ParticipantProfile.objects.count()
        instructor_count = InstructorProfile.objects.count()
        seminar_count = Seminar.objects.count()

        # assertCountEqual()은 순서 상관 없이 같은 원소인지만 check
        self.assertListEqual([user_count, participant_count, instructor_count, seminar_count], [3, 2, 1, 1])

        seminar1 = Seminar.objects.first()

        response = self.client.get(
            '/api/v1/seminar/{}/'.format(seminar1.id),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_invalid_seminar_id(self):
        response = self.client.get(
            '/api/v1/seminar/0/',
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant1_token
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GetSeminarTestCase(TestCase):
    client = Client()

    def setUp(self):
        # participant1
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant1",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.participant1_token = 'Token ' + Token.objects.get(user__username='participant1').key

        # participant2
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant2",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.participant2_token = 'Token ' + Token.objects.get(user__username='participant2').key

        # instructor1
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "instructor1",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "instructor",
                "company": "orangenongjang",
                "year": 1
            }),
            content_type='application/json'
        )
        self.instructor1_token = 'Token ' + Token.objects.get(user__username='instructor1').key

        # instructor2
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "instructor2",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "instructor",
                "company": "orangenongjang",
                "year": 1
            }),
            content_type='application/json'
        )
        self.instructor2_token = 'Token ' + Token.objects.get(user__username='instructor2').key

    def test_get_Seminar_request(self):
        # seminar1
        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "Bayesian",
                "time": "14:30",
                "online": True,
                "count": 3,
                "capacity": 2
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # seminar2
        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "Archaeology",
                "time": "12:12",
                "online": True,
                "count": 3,
                "capacity": 2,
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        seminar = Seminar.objects.all()
        self.assertEqual(seminar.count(), 2)
        data = response.json()
        # Because of order_by('-created_at'), the order should be reverse.
        self.assertEqual(data["id"], Seminar.objects.last().id)
        self.assertNotEqual(data["id"], Seminar.objects.first().id)

        # enroll seminar
        response = self.client.post(
            '/api/v1/user/participant/',
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            '/api/v1/seminar/{}/user/'.format(data["id"]),
            json.dumps({
                "role": "participant",
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(
            '/api/v1/seminar/',
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]["id"], Seminar.objects.last().id)
        self.assertEqual(data[0]["participant_count"], 1)
        self.assertEqual(data[1]["participant_count"], 0)

        # query params : name (upper case)
        name = "B"
        response = self.client.get(
            '/api/v1/seminar/?name={}'.format(name),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]["name"], "Bayesian")
        self.assertEqual(len(data), 1)

        # query params : name (lower case)
        name = "b"
        response = self.client.get(
            '/api/v1/seminar/?name={}'.format(name),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]["name"], "Bayesian")
        self.assertEqual(len(data), 1)

        # query params : name (blank)
        name = ""
        response = self.client.get(
            '/api/v1/seminar/?name={}'.format(name),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]["name"], "Archaeology")
        self.assertEqual(len(data), 2)

        # query params : name (no matching)
        name = "z"
        response = self.client.get(
            '/api/v1/seminar/?name={}'.format(name),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, [])

        # query params : order=earliest
        order = "earliest"
        response = self.client.get(
            '/api/v1/seminar/?order={}'.format(order),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]["id"], Seminar.objects.first().id)
        self.assertListEqual([data[0]["participant_count"], data[1]["participant_count"]], [0, 1])

        # query params : order=early (typo)
        order = "early"
        response = self.client.get(
            '/api/v1/seminar/?order={}'.format(order),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]["id"], Seminar.objects.last().id)
        self.assertListEqual([data[0]["participant_count"], data[1]["participant_count"]], [1, 0])

        # query params : name & order=earliest
        name = "B"
        order = "earliest"
        response = self.client.get(
            '/api/v1/seminar/?name={}&order={}'.format(name, order),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]["name"], "Bayesian")
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], Seminar.objects.first().id)

    def test_get_no_Seminar_request(self):
        # No Seminar
        response = self.client.get(
            '/api/v1/seminar/',

            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Seminar.objects.exists())
        self.assertEqual(Seminar.objects.count(), 0)

        # Invalid token
        response = self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "Bayesian",
                "time": "14:30",
                "online": True,
                "count": 3,
                "capacity": 2
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(
            '/api/v1/seminar/',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PostSeminarIdUserTestCase(TestCase):
    client = Client()

    def setUp(self):
        # participant1
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant1",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.participant1_token = 'Token ' + Token.objects.get(user__username='participant1').key

        # participant2
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant2",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.participant2_token = 'Token ' + Token.objects.get(user__username='participant2').key

        # instructor1
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "instructor1",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "instructor",
                "company": "orangenongjang",
                "year": 1
            }),
            content_type='application/json'
        )
        self.instructor1_token = 'Token ' + Token.objects.get(user__username='instructor1').key

        # instructor2
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "instructor2",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "instructor",
                "company": "orangenongjang",
                "year": 1
            }),
            content_type='application/json'
        )
        self.instructor2_token = 'Token ' + Token.objects.get(user__username='instructor2').key

        # instructor3
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "instructor3",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "instructor",
                "company": "orangenongjang",
                "year": 1
            }),
            content_type='application/json'
        )
        self.instructor3_token = 'Token ' + Token.objects.get(user__username='instructor3').key

        # seminar1
        self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "Bayesian",
                "time": "14:30",
                "online": True,
                "count": 3,
                "capacity": 2
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )

        # seminar2
        self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "Data Mining",
                "time": "09:30",
                "online": True,
                "count": 3,
                "capacity": 1
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )

    def test_valid_post_seminar_user(self):
        seminars = Seminar.objects.all()

        # 최신순으로 배열되는 body와 다르게 seminars 객체 리스트는 오래된 순서임에 유의할 것.
        self.assertEqual(seminars[0].name, "Bayesian")

        # charge가 없는 instructor가 instructor로 세미나 신청하는 경우
        response = self.client.post(
            '/api/v1/seminar/{}/user/'.format(seminars[0].id),
            json.dumps({
                "role": "instructor"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor3_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 세미나 담당이 아닌 instructor가 participant로 세미나 신청하는 경우 (participant role 획득 후)
        response = self.client.post(
            '/api/v1/user/participant/',
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            '/api/v1/seminar/{}/user/'.format(seminars[0].id),
            json.dumps({
                "role": "participant"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(seminars[0].users.filter(role="participant").count(), 1)
        self.assertGreaterEqual(seminars[0].capacity, seminars[0].users.filter(role="participant").count())

        # 참여하지 않은 participant가 신청하는 경우
        response = self.client.post(
            '/api/v1/seminar/{}/user/'.format(seminars[0].id),
            json.dumps({
                "role": "participant"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant1_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_post_seminar_user(self):
        seminars = Seminar.objects.all()

        # Role must be 'instructor' or 'participant'
        response = self.client.post(
            '/api/v1/seminar/{}/user/'.format(seminars[0].id),
            json.dumps({
                "role": "participants"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # The instructor should get 'participant' role first.
        response = self.client.post(
            '/api/v1/seminar/{}/user/'.format(seminars[0].id),
            json.dumps({
                "role": "participant"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor3_token
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # You've been already charged of another seminar.
        response = self.client.post(
            '/api/v1/seminar/{}/user/'.format(seminars[0].id),
            json.dumps({
                "role": "instructor"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # The seminar is beyond capacity.
        response = self.client.post(
            '/api/v1/seminar/{}/user/'.format(seminars[1].id),
            json.dumps({
                "role": "participant"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant1_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(seminars[1].users.count(), seminars[1].capacity)

        response = self.client.post(
            '/api/v1/seminar/{}/user/'.format(seminars[1].id),
            json.dumps({
                "role": "participant"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant2_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # The user who've dropped cannot enroll in the same seminar
        response = self.client.delete(
            '/api/v1/seminar/{}/user/'.format(seminars[1].id),
            json.dumps({
                "role": "participant"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            '/api/v1/seminar/{}/user/'.format(seminars[1].id),
            json.dumps({
                "role": "participant"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant1_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteSeminarIdUserTestCase(TestCase):
    client = Client()

    def setUp(self):
        # participant1
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant1",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.participant1_token = 'Token ' + Token.objects.get(user__username='participant1').key

        # participant2
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant2",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.participant2_token = 'Token ' + Token.objects.get(user__username='participant2').key

        # instructor1
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "instructor1",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "instructor",
                "company": "orangenongjang",
                "year": 1
            }),
            content_type='application/json'
        )
        self.instructor1_token = 'Token ' + Token.objects.get(user__username='instructor1').key

        # seminar1
        self.client.post(
            '/api/v1/seminar/',
            json.dumps({
                "name": "Bayesian",
                "time": "14:30",
                "online": True,
                "count": 3,
                "capacity": 2
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )

        seminar1 = Seminar.objects.last()
        self.assertEqual(seminar1.name, "Bayesian")

        response = self.client.post(
            '/api/v1/seminar/{}/user/'.format(seminar1.id),
            json.dumps({
                "role": "participant"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant1_token
        )

        self.client.post(
            '/api/v1/seminar/{}/user/'.format(seminar1.id),
            json.dumps({
                "role": "participant"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant2_token
        )
        self.assertEqual(UserSeminar.objects.count(), 3)
        self.assertEqual(UserSeminar.objects.filter(role="participant").count(), 2)

    def test_valid_delete_seminar_user(self):
        response = self.client.delete(
            '/api/v1/seminar/{}/user/'.format(Seminar.objects.last().id),
            json.dumps({
                "role": "participant"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_delete_seminar_user(self):
        # The instructor cannot drop the seminar.
        response = self.client.delete(
            '/api/v1/seminar/{}/user/'.format(Seminar.objects.last().id),
            json.dumps({
                "role": "participant"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
