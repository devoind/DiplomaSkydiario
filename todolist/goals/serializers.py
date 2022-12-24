from django.db import transaction
from rest_framework import serializers, exceptions

from core.models import User
from core.serializers import UserSerializer
from goals.models import GoalCategory, Goal, GoalComment, Board, BoardParticipant


# Boards
class BoardCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Board
        fields = '__all__'
        read_only_fields = ['id', 'created', 'updated']

    def create(self, validated_data):
        user = validated_data.pop("user")
        board = Board.objects.create(**validated_data)
        BoardParticipant.objects.create(user=user, board=board, role=BoardParticipant.Role.owner)
        return board


class BoardParticipantSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(required=True, choices=BoardParticipant.editable_choices)
    user = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())

    class Meta:
        model = BoardParticipant
        fields = '__all__'
        read_only_fields = ['id', 'created', 'updated', 'board']


class BoardSerializer(serializers.ModelSerializer):
    participants = BoardParticipantSerializer(many=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Board
        fields = '__all__'
        read_only_fields = ['id', 'created', 'updated']

    def update(self, instance, validated_data):
        owner = validated_data.pop('user')
        new_participants = validated_data.pop('participants')
        with transaction.atomic():
            for part in new_participants:
                new_part_ids = {part['user'].id: part}

            old_participants = instance.participants.exclude(user=owner)

            for old_participant in old_participants:
                if old_participant.user_id not in new_part_ids:
                    old_participant.delete()
                else:
                    if old_participant.role != new_part_ids[old_participant.user_id]['role']:
                        old_participant.role = new_part_ids[old_participant.user_id]['role']
                        old_participant.save()
                    new_part_ids.pop(old_participant.user_id)
            for new_part in new_part_ids.values():
                BoardParticipant.objects.create(board=instance, user=new_part['user'], role=new_part['role'])
            instance.title = validated_data['title']
            instance.save()

        return instance


class BoardListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = '__all__'


# GoalCategories
class GoalCategoryCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = GoalCategory
        read_only_fields = ['id', 'created', 'updated', 'user', 'is_deleted']
        fields = '__all__'

    def validate_board(self, value):
        if value.is_deleted:
            raise serializers.ValidationError("not allowed for deleted board")
        allowed = BoardParticipant.objects.filter(
            board=value.id,
            role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
            user=self.context["request"].user,
        ).exists()
        if not allowed:
            raise serializers.ValidationError("must be owner or writer of the board")
        return value


class GoalCategorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = GoalCategory
        fields = '__all__'
        read_only_fields = ['id', 'created', 'updated', 'user', 'board']


# Goals
class GoalCreateSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=GoalCategory.objects.filter(is_deleted=False)
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ['id', 'created', 'updated', 'user']

    def validate_category(self, value):
        if value.is_deleted:
            raise serializers.ValidationError('not allowed in deleted category')

        allowed = BoardParticipant.objects.filter(
            board_id=value.board_id,
            role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
            user=self.context["request"].user,
        ).exists()
        if not allowed:
            raise serializers.ValidationError("must be owner or writer of the goal")
        return value


class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ['id', 'created', 'updated', 'user']

    def validate_category(self, value):
        # if self.context['request'].user.id != value.user_id:
        #     raise exceptions.PermissionDenied
        if value.is_deleted:
            raise serializers.ValidationError('not allowed in deleted category')

        return value


# GoalComments
class GoalCommentCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    goal = serializers.PrimaryKeyRelatedField(
        queryset=Goal.objects.all()
    )

    class Meta:
        model = GoalComment
        fields = '__all__'
        read_only_fields = ['id', 'created', 'updated', 'user']

    def validate_goal(self, value):
        allowed = BoardParticipant.objects.filter(
            board_id=value.category.board_id,
            role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
            user=self.context["request"].user,
        ).exists()
        if not allowed:
            raise serializers.ValidationError("must be owner or writer of the goal")
        return value


class GoalCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = GoalComment
        fields = '__all__'
        read_only_fields = ['id', 'created', 'updated', 'user', 'goal']
