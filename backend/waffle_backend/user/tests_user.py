from django.contrib.auth.models import User
from django.test import Client, TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
import json

from user.models import InstructorProfile, ParticipantProfile


class PostUserTestCase(TestCase):
    client = Client()

    def setUp(self):
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "davin111",
                "password": "password",
                "first_name": "Davin",
                "last_name": "Byeon",
                "email": "bdv111@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )

    def test_post_user_duplicated_username(self):
        response = self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "davin111",
                "password": "password",
                "first_name": "Davin",
                "last_name": "Byeon",
                "email": "bdv111@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

    def test_post_user_incomplete_request(self):
        response = self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant",
                "password": "password",
                "first_name": "Davin",
                "last_name": "Byeon",
                "email": "bdv111@snu.ac.kr",
                "role": "wrong_role",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant",
                "password": "password",
                "first_name": "Davin",
                "last_name": "Byeon",
                "email": "bdv111@snu.ac.kr",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant",
                "password": "password",
                "first_name": "Davin",
                "last_name": "Byeon",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

    def test_post_user(self):
        response = self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "davin111",
                "password": "password",
                "first_name": "Davin",
                "last_name": "Byeon",
                "email": "bdv111@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

        response = self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant",
                "password": "password",
                "first_name": "Davin",
                "last_name": "Byeon",
                "email": "bdv111@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["username"], "participant")
        self.assertEqual(data["email"], "bdv111@snu.ac.kr")
        self.assertEqual(data["first_name"], "Davin")
        self.assertEqual(data["last_name"], "Byeon")
        self.assertIn("last_login", data)
        self.assertIn("date_joined", data)
        self.assertIn("token", data)

        participant = data["participant"]
        self.assertIsNotNone(participant)
        self.assertIn("id", participant)
        self.assertEqual(participant["university"], "SNU")
        self.assertTrue(participant["accepted"])
        self.assertEqual(len(participant["seminars"]), 0)

        self.assertIsNone(data["instructor"])

        user_count = User.objects.count()
        participant_count = ParticipantProfile.objects.count()
        instructor_count = InstructorProfile.objects.count()
        self.assertCountEqual([user_count, participant_count, instructor_count], [2, 2, 0])


class PutUserLoginTestCase(TestCase):
    client = Client()

    def setUp(self):
        # User.objects.create is not good because of unnecessary request fields such as role, university, etc.
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant1",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "KO",
                "email": "newstellar@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        participant_user = User.objects.get(username='participant1')
        self.assertEqual(participant_user.first_name, 'yeonghyeon')

        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "instructor1",
                "password": "1234",
                "first_name": "Marcel",
                "last_name": "KO",
                "email": "newstellar@snu.ac.kr",
                "role": "instructor",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        instructor_user = User.objects.get(username='instructor1')
        self.assertEqual(instructor_user.first_name, 'Marcel')
        self.assertEqual(User.objects.count(), 2)

    def test_put_user_forbidden_login(self):
        response = self.client.put(
            '/api/v1/user/login/',
            json.dumps({
                "username": "participant1"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(
            '/api/v1/user/login/',
            json.dumps({
                "password": "1234"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(
            '/api/v1/user/login/',
            json.dumps({
                "username": "participant111"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(
            '/api/v1/user/login/',
            json.dumps({
                "username": "participant1",
                "password": "123456"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_user_login(self):
        response = self.client.put(
            '/api/v1/user/login/',
            json.dumps({
                "username": "participant1",
                "password": "1234"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        last = User.objects.order_by('last_login').last()
        self.assertEqual(last.username, 'participant1')


class PutUserMeTestCase(TestCase):
    client = Client()

    def setUp(self):
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "part",
                "password": "password",
                "first_name": "Davin",
                "last_name": "Byeon",
                "email": "bdv111@snu.ac.kr",
                "role": "participant",
                "university": "SNU"
            }),
            content_type='application/json'
        )
        self.participant_token = 'Token ' + Token.objects.get(user__username='part').key

        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "inst",
                "password": "password",
                "first_name": "Davin",
                "last_name": "Byeon",
                "email": "bdv111@snu.ac.kr",
                "role": "instructor",
                "year": 1
            }),
            content_type='application/json'
        )
        self.instructor_token = 'Token ' + Token.objects.get(user__username='inst').key

    def test_put_user_incomplete_request(self):
        response = self.client.put(
            '/api/v1/user/me/',
            json.dumps({
                "first_name": "Dabin"
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.put(
            '/api/v1/user/me/',
            json.dumps({
                "first_name": "Dabin"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        participant_user = User.objects.get(username='part')
        self.assertEqual(participant_user.first_name, 'Davin')

        response = self.client.put(
            '/api/v1/user/me/',
            json.dumps({
                "username": "inst123",
                "email": "bdv111@naver.com",
                "company": "매스프레소",
                "year": -1
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        instructor_user = User.objects.get(username='inst')
        self.assertEqual(instructor_user.email, 'bdv111@snu.ac.kr')

    def test_put_user_me_participant(self):
        response = self.client.put(
            '/api/v1/user/me/',
            json.dumps({
                "username": "part123",
                "email": "bdv111@naver.com",
                "university": "KNU"
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["username"], "part123")
        self.assertEqual(data["email"], "bdv111@naver.com")
        self.assertEqual(data["first_name"], "Davin")
        self.assertEqual(data["last_name"], "Byeon")
        self.assertIn("last_login", data)
        self.assertIn("date_joined", data)
        self.assertNotIn("token", data)

        participant = data["participant"]
        self.assertIsNotNone(participant)
        self.assertIn("id", participant)
        self.assertEqual(participant["university"], "KNU")
        self.assertTrue(participant["accepted"])
        self.assertEqual(len(participant["seminars"]), 0)

        self.assertIsNone(data["instructor"])
        participant_user = User.objects.get(username='part123')
        self.assertEqual(participant_user.email, 'bdv111@naver.com')

    def test_put_user_me_instructor(self):
        response = self.client.put(
            '/api/v1/user/me/',
            json.dumps({
                "username": "inst123",
                "email": "bdv111@naver.com",
                "first_name": "Dabin",
                "last_name": "Byeon",
                "university": "SNU",  # this should be ignored
                "company": "MATHPRESSO",
                "year": 2
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["username"], "inst123")
        self.assertEqual(data["email"], "bdv111@naver.com")
        self.assertEqual(data["first_name"], "Dabin")
        self.assertEqual(data["last_name"], "Byeon")
        self.assertIn("last_login", data)
        self.assertIn("date_joined", data)
        self.assertNotIn("token", data)

        self.assertIsNone(data["participant"])

        instructor = data["instructor"]
        self.assertIsNotNone(instructor)
        self.assertIn("id", instructor)
        self.assertEqual(instructor["company"], "MATHPRESSO")
        self.assertEqual(instructor["year"], 2)
        self.assertIsNone(instructor["charge"])

        instructor_user = User.objects.get(username='inst123')
        self.assertEqual(instructor_user.email, 'bdv111@naver.com')


class GetUserIdTestCase(TestCase):
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

        # participant2 (no university)
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "participant2",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "participant"
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

        # instructor2 (neither company nor year)
        self.client.post(
            '/api/v1/user/',
            json.dumps({
                "username": "instructor2",
                "password": "1234",
                "first_name": "yeonghyeon",
                "last_name": "Ko",
                "email": "newstellar@snu.ac.kr",
                "role": "instructor"
            }),
            content_type='application/json'
        )
        self.instructor2_token = 'Token ' + Token.objects.get(user__username='instructor2').key

        user_count = User.objects.count()
        participant_count = ParticipantProfile.objects.count()
        instructor_count = InstructorProfile.objects.count()
        self.assertCountEqual([user_count, participant_count, instructor_count], [4, 2, 2])

    def test_get_valid_user_id(self):
        participant1 = ParticipantProfile.objects.first()
        participant2 = ParticipantProfile.objects.last()
        instructor1 = InstructorProfile.objects.first()
        instructor2 = InstructorProfile.objects.last()

        # participant1
        response = self.client.get(
            '/api/v1/user/{}/'.format(participant1.user.id),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("id", data)
        self.assertIn("university", data["participant"])
        self.assertEqual(data["participant"]["seminars"], [])
        self.assertIsNone(data["instructor"])
        self.assertEqual(data["username"], "participant1")
        self.assertEqual(User.objects.filter(username=data["username"]).last().id, participant1.user_id)
        self.assertEqual(data["participant"]["university"], participant1.university)

        # participant2
        response = self.client.get(
            '/api/v1/user/{}/'.format(participant2.user.id),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant2_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("id", data)
        self.assertIsNotNone(participant2.university)
        self.assertEqual(participant2.university, "")

        # instructor1
        response = self.client.get(
            '/api/v1/user/{}/'.format(instructor1.user.id),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("id", data)
        self.assertIn("company", data["instructor"])
        self.assertIn("year", data["instructor"])
        self.assertIsNone(data["instructor"]["charge"])
        self.assertIsNone(data["participant"])
        self.assertEqual(data["username"], "instructor1")
        self.assertEqual(User.objects.filter(username=data["username"]).last().id, instructor1.user_id)
        self.assertEqual(data["instructor"]["company"], instructor1.company)
        self.assertEqual(data["instructor"]["year"], instructor1.year)

        # instructor2
        response = self.client.get(
            '/api/v1/user/{}/'.format(instructor2.user.id),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("id", data)
        self.assertIsNotNone(instructor2.company)
        self.assertEqual(instructor2.company, "")
        self.assertEqual(instructor2.year, None)

        # Using other user's Token
        response = self.client.get(
            '/api/v1/user/{}/'.format(participant1.user.id),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant2_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_invalid_user_id(self):
        participant1 = ParticipantProfile.objects.first()

        response = self.client.get(
            '/api/v1/user/{}/'.format(participant1.user.id),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor2_token + "a"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GetUserMeTestCase(TestCase):
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

        user_count = User.objects.count()
        participant_count = ParticipantProfile.objects.count()
        instructor_count = InstructorProfile.objects.count()
        self.assertCountEqual([user_count, participant_count, instructor_count], [2, 1, 1])

    def test_get_valid_user_me(self):
        participant1 = ParticipantProfile.objects.first()
        instructor1 = InstructorProfile.objects.first()

        # E.T.S. 200 status code and whether query is valid
        # participant1
        response = self.client.get(
            '/api/v1/user/me/',
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(User.objects.filter(username=data["username"]).last().id, participant1.user_id)

        # instructor1
        response = self.client.get(
            '/api/v1/user/me/',
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(User.objects.filter(username=data["username"]).last().id, instructor1.user_id)

    def test_get_invalid_user_me(self):
        # Check when token is invalid
        # No Token
        response = self.client.get(
            '/api/v1/user/me/',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Typo
        response = self.client.get(
            '/api/v1/user/me/',
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token + "a"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PostUserParticipantTestCase(TestCase):
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

    def test_post_user_participant_failed(self):
        # No Token
        response = self.client.post(
            '/api/v1/user/participant/',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # The participant's Token, not the instructor's
        response = self.client.post(
            '/api/v1/user/participant/',
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant1_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_user_participant(self):
        self.assertEqual(ParticipantProfile.objects.count(), 1)

        response = self.client.post(
            '/api/v1/user/participant/',
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor1_token
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ParticipantProfile.objects.count(), 2)
