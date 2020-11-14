from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import transaction
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from seminar.models import Seminar, UserSeminar
from user.models import InstructorProfile, ParticipantProfile


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(allow_blank=False)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    last_login = serializers.DateTimeField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    instructor = serializers.SerializerMethodField()
    participant = serializers.SerializerMethodField()
    role = serializers.ChoiceField(choices=UserSeminar.ROLES, write_only=True)
    company = serializers.CharField(allow_blank=True, required=False, write_only=True)
    year = serializers.IntegerField(required=False, write_only=True, validators=[MinValueValidator(0)])
    university = serializers.CharField(allow_blank=True, required=False, write_only=True)
    accepted = serializers.BooleanField(default=True, required=False, write_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'last_login',
            'date_joined',
            'participant',
            'instructor',
            'role',
            'company',
            'year',
            'university',
            'accepted',
        )

    def validate_password(self, value):
        return make_password(value)

    def validate(self, data):
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        if bool(first_name) ^ bool(last_name):
            raise serializers.ValidationError("First name and last name should appear together.")
        if first_name and last_name and not (first_name.isalpha() and last_name.isalpha()):
            raise serializers.ValidationError("First name or last name should not have number.")

        role = data.get('role')
        if role == UserSeminar.INSTRUCTOR:
            profile_serializer = InstructorProfileSerializer(data=data, context=self.context)
        else:
            profile_serializer = ParticipantProfileSerializer(data=data, context=self.context)
        profile_serializer.is_valid(raise_exception=True)
        return data

    @transaction.atomic
    def create(self, validated_data):
        role = validated_data.pop('role')
        company = validated_data.pop('company', '')
        year = validated_data.pop('year', None)
        university = validated_data.pop('university', '')
        accepted = validated_data.pop('accepted', None)

        user = super(UserSerializer, self).create(validated_data)
        Token.objects.create(user=user)
        if role == UserSeminar.INSTRUCTOR:
            InstructorProfile.objects.create(user=user, company=company, year=year)
        else:
            ParticipantProfile.objects.create(user=user, university=university, accepted=accepted)
        return user

    @transaction.atomic
    def update(self, user, validated_data):
        user = super(UserSerializer, self).update(user, validated_data)
        if hasattr(user, 'instructor'):
            instructor = user.instructor
            company = validated_data.get('company')
            year = validated_data.get('year')
            if company is not None:
                instructor.comapny = company
            if validated_data.get('year'):
                instructor.year = validated_data.get('year')
            else:
                instructor.year = None
            if validated_data.get('company'):
                instructor.company = validated_data.get('company')
            else:
                instructor.company = ''
            instructor.save()

        if hasattr(user, 'participant'):
            participant = user.participant
            if validated_data.get('university'):
                participant.university = validated_data.get('university')
            else:
                participant.university = ''
            participant.save()
        return user

    def get_instructor(self, user):
        if hasattr(user, 'instructor'):
            return InstructorProfileSerializer(user.instructor, context=self.context).data
        return None

    def get_participant(self, user):
        if hasattr(user, 'participant'):
            return ParticipantProfileSerializer(user.participant, context=self.context).data
        return None


class InstructorProfileSerializer(serializers.ModelSerializer):
    charge = serializers.SerializerMethodField()

    class Meta:
        model = InstructorProfile
        fields = (
            'id',
            'company',
            'year',
            'charge',
        )

    def get_charge(self, instructor):
        if instructor.charge:
            return ChargeSerializer(instructor.charge, context=self.context).data
        return None


class ChargeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    joined_at = serializers.DateTimeField(source='created_at')

    class Meta:
        model = Seminar
        fields = (
            'id',
            'name',
            'joined_at',
        )

    def get_name(self, seminar):
        return seminar.name


class ParticipantProfileSerializer(serializers.ModelSerializer):
    seminars = serializers.SerializerMethodField()

    class Meta:
        model = ParticipantProfile
        fields = (
            'id',
            'university',
            'accepted',
            'seminars',
        )

    def get_seminars(self, participant):
        seminars = []
        participants = UserSeminar.objects.filter(user=participant.user)
        for participant in participants:
            seminars.append(participant.seminar)
        return SeminarsSerializer(seminars, many=True, context=self.context).data


class SeminarsSerializer(serializers.ModelSerializer):
    joined_at = serializers.DateTimeField(source='created_at')
    is_active = serializers.SerializerMethodField()
    dropped_at = serializers.SerializerMethodField()

    class Meta:
        model = Seminar
        fields = (
            'id',
            'name',
            'joined_at',
            'is_active',
            'dropped_at',
        )

    def get_is_active(self, seminar):
        return seminar.users.last().is_active if seminar else None

    def get_dropped_at(self, seminar):
        return seminar.users.last().dropped_at if seminar else None
