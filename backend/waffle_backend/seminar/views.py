from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from seminar.models import Seminar, UserSeminar
from seminar.serializers import SeminarSerializer, SimpleSeminarSerializer
from user.models import InstructorProfile, ParticipantProfile


class SeminarViewSet(viewsets.GenericViewSet):
    queryset = Seminar.objects.all()
    serializer_class = SeminarSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'list':
            return SimpleSeminarSerializer
        return self.serializer_class

    # POST /api/v1/seminar/
    def create(self, request):
        user = request.user
        try:
            instructor = InstructorProfile.objects.get(user=user)
        except ObjectDoesNotExist:
            return Response({"error": "Only instructor can open the seminar."}, status=status.HTTP_403_FORBIDDEN)

        try:
            if not instructor.charge:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": "You're in charge of another seminar."}, status=status.HTTP_403_FORBIDDEN)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    # GET /api/v1/seminar/?name={name}&order=earliest
    def list(self, request):
        seminar_order = self.request.query_params.get('order')
        seminar_name = self.request.query_params.get('name')
        queryset = self.get_queryset().order_by('-created_at')
        if not queryset:
            Response(status=status.HTTP_404_NOT_FOUND)

        cache_key = 'seminars'
        if seminar_order != 'earliest':
            seminars = cache.get(cache_key)
            if seminars is None:
                cache.set(cache_key, queryset, timeout=10)
                seminars = cache.get(cache_key)
            if seminar_name is not None:
                seminars = seminars.filter(name__icontains=seminar_name)
        else:
            seminars = cache.get(cache_key, version=2)
            if seminars is None:
                queryset = self.get_queryset().order_by('created_at')
                cache.set(cache_key, queryset, timeout=600, version=2)
                seminars = cache.get(cache_key, version=2)
            if seminar_name is not None:
                seminars = seminars.filter(name__icontains=seminar_name)
        return Response(self.get_serializer(seminars, many=True).data)

    # GET /api/v1/seminar/{seminar_id}/
    def retrieve(self, request, pk=None):
        seminar = self.get_object()
        seminar.time = seminar.time.isoformat(timespec='minutes')

        if not seminar:
            return Response(status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(seminar).data)

    @transaction.atomic
    # PUT /api/v1/seminar/{seminar_id}/
    def update(self, request, pk=None):
        seminar = self.get_object()
        seminar.name = request.data.get('name')
        if not seminar.name:
            return Response({"error": "The name of seminar cannot be blank"}, status=status.HTTP_400_BAD_REQUEST)

        instructor = InstructorProfile.objects.filter(user_id=request.user.id)
        if not instructor:
            return Response({"error": "Only instructor of seminar can change its information"},
                            status=status.HTTP_403_FORBIDDEN)
        seminar.count = int(request.data.get('count', seminar.count))
        if seminar.users.filter(role=UserSeminar.PARTICIPANT).count() <= int(request.data.get('capacity', seminar.capacity)):
            seminar.capacity = request.data.get('capacity', seminar.capacity)
        else:
            return Response({"error": "The capacity must be not less than the number of participants"},
                            status=status.HTTP_400_BAD_REQUEST)
        seminar.time = request.data.get('time', seminar.time)
        seminar.online = request.data.get('online', seminar.online)
        seminar.save()
        return Response(self.get_serializer(seminar).data)

    @transaction.atomic
    @action(methods=['POST', 'DELETE'], detail=True, url_path='user', url_name='user')
    def enroll_drop(self, request, pk=None):

        # POST /api/v1/seminar/{seminar_id}/user/
        if request.method == 'POST':
            data = request.data.copy()
            role = data.get("role")
            if role not in UserSeminar.ROLES:
                return Response({'error': "Role must be 'instructor' or 'participant'"},
                                status=status.HTTP_400_BAD_REQUEST)

            seminar = self.get_object()
            user = request.user
            if not user.is_authenticated:
                return Response(status=status.HTTP_403_FORBIDDEN)

            try:
                if role == UserSeminar.INSTRUCTOR:
                    if user.instructor.charge_id:
                        return Response({'error': "You've been already charged of another seminar."},
                                        status=status.HTTP_400_BAD_REQUEST)
                    UserSeminar.objects.get_or_create(user=user, seminar=seminar, role="instructor")
                    user.instructor.charge_id = seminar.id
                    user.instructor.save()

                if role == UserSeminar.PARTICIPANT:
                    if seminar.capacity <= UserSeminar.objects.filter(seminar=seminar, role="participant",
                                                                      is_active=True).count():
                        return Response({'error': "The seminar is beyond capacity."},
                                        status=status.HTTP_400_BAD_REQUEST)
                    try:
                        if user.participant:
                            try:
                                if user.instructor.charge_id == seminar.id:
                                    return Response({'error': "You're the instructor of this seminar."},
                                                    status=status.HTTP_403_FORBIDDEN)
                            except InstructorProfile.DoesNotExist:
                                pass
                    except ParticipantProfile.DoesNotExist:
                        return Response({'error': "The instructor should get 'participant' role first."},
                                        status=status.HTTP_403_FORBIDDEN)

                    if not UserSeminar.objects.filter(role=UserSeminar.PARTICIPANT, user_id=user.id).exists():
                        UserSeminar.objects.create(user=user, seminar=seminar, role="participant")
                        participant = ParticipantProfile.objects.get(user=user)
                    else:
                        if not user.seminars.get(seminar=seminar).is_active:
                            return Response({'error': "The user who've dropped cannot enroll in the same seminar"},
                                            status=status.HTTP_400_BAD_REQUEST)

                        return Response({'error': "You've been already included in the seminar."},
                                        status=status.HTTP_400_BAD_REQUEST)

                    if not participant.accepted:
                        return Response({'error': "Your request cannot be accepted."},
                                        status=status.HTTP_403_FORBIDDEN)

            except ObjectDoesNotExist:
                return Response({'error': "Have you check your role?"},
                                status=status.HTTP_403_FORBIDDEN)

            seminar = self.get_object()
            serializer = self.get_serializer(seminar)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE /api/v1/seminar/{seminar_id}/user/
        if self.request.method == 'DELETE':
            user = request.user
            seminar = self.get_object()
            try:
                if user.participant:
                    participant = user.seminars.filter(seminar_id=seminar.id, role="participant").last()

                    if participant is None:
                        try:
                            if user.instructor.charge_id == seminar.id:
                                return Response({'error': "The instructor cannot drop the seminar"},
                                                status=status.HTTP_403_FORBIDDEN)
                            else:
                                Response({'error': "You've never enrolled this seminar."},
                                         status=status.HTTP_400_BAD_REQUEST)
                        except ObjectDoesNotExist:
                            return Response({'error': "You've never enrolled this seminar."},
                                            status=status.HTTP_400_BAD_REQUEST)
                    participant.is_active = False
                    participant.dropped_at = timezone.now()
                    participant.save()

            except ObjectDoesNotExist:
                return Response({'error': "The instructor cannot drop the seminar."},
                                status=status.HTTP_403_FORBIDDEN)

            seminar = self.get_object()
            serializer = self.get_serializer(seminar)
            return Response(serializer.data)
