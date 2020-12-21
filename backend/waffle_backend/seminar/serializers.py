from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction

from seminar.models import Seminar, UserSeminar
from user.models import InstructorProfile


class SeminarSerializer(serializers.ModelSerializer):
    instructors = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()
    time = serializers.TimeField(input_formats=["%H:%M"])

    class Meta:
        model = Seminar
        fields = (
            'id',
            'name',
            'capacity',
            'count',
            'time',
            'online',
            'instructors',
            'participants',
        )

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        instructor = InstructorProfile.objects.get(user=user)
        if instructor:
            validated_data['time'] = validated_data.get('time').isoformat(timespec='minutes')
            seminar = super(SeminarSerializer, self).create(validated_data)
            UserSeminar.objects.create(user=user, seminar=seminar, role=UserSeminar.INSTRUCTOR)
            instructor.charge_id = seminar.id
            instructor.save()
            return seminar
        else:
            return None

    def get_instructors(self, seminar):
        instructors = seminar.users.filter(role=UserSeminar.INSTRUCTOR)
        return InstructorsSerializer(instructors, context=self.context, many=True).data

    def get_participants(self, seminar):
        participants = seminar.users.filter(role=UserSeminar.PARTICIPANT)
        return ParticipantsSerializer(participants, context=self.context, many=True).data


class SimpleSeminarSerializer(serializers.ModelSerializer):
    instructors = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Seminar
        fields = (
            'id',
            'name',
            'instructors',
            'participant_count'
        )

    def get_instructors(self, seminar):
        instructors = seminar.users.filter(role=UserSeminar.INSTRUCTOR)
        return InstructorsSerializer(instructors, context=self.context, many=True).data

    def get_participant_count(self, seminar):
        return seminar.users.filter(role=UserSeminar.PARTICIPANT, is_active=True).count()


class InstructorsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id')
    username = serializers.DateTimeField(source='user.username')
    email = serializers.DateTimeField(source='user.email')
    first_name = serializers.DateTimeField(source='user.first_name')
    last_name = serializers.DateTimeField(source='user.last_name')
    joined_at = serializers.DateTimeField(source='created_at')

    class Meta:
        model = UserSeminar
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'joined_at',
        )


class ParticipantsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id')
    username = serializers.DateTimeField(source='user.username')
    email = serializers.DateTimeField(source='user.email')
    first_name = serializers.DateTimeField(source='user.first_name')
    last_name = serializers.DateTimeField(source='user.last_name')
    joined_at = serializers.DateTimeField(source='created_at')

    class Meta:
        model = UserSeminar
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'joined_at',
            'is_active',
            'dropped_at',
        )
