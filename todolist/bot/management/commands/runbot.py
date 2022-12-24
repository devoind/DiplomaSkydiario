from dataclasses import dataclass
from typing import Union

from django.conf import settings
from django.core.management import BaseCommand
from django.db.models import QuerySet

from bot.models import TgUser
from bot.tg.client import TgClient
from goals.models import Goal, GoalCategory, BoardParticipant
from todolist.settings import TG_BOT_TOKEN


@dataclass
class OperationState:
    normal = ['normal', 'No pending operations']
    input_required = ['input', 'Awaiting input']

    def __getitem__(self, item):
        return item


@dataclass
class SubOperation:
    initial = ['initial', 'Initial']
    title_input = ['name', 'Title prompt']
    category_id_input = ['id', 'Category id prompt']
    none = ['none', 'No pending sub operations']

    def __getitem__(self, item):
        return item


@dataclass
class CurrentOperation:
    goal_create = ['goal_create', 'Goal creation']
    category_create = ['category_create', 'Category creation']
    none = ['none', 'No pending operations']

    def __getitem__(self, item):
        return item


class OperationBuffer:
    tg_user: TgUser = None
    current_operation: CurrentOperation = None
    operation_state: OperationState = OperationState.normal
    sub_operation: SubOperation = SubOperation.none
    user_input: Union[str, int, None] = None
    valid_input: Union[list[Union[str, int]], None] = []
    category_id_input: int = None
    goal_title: str = None

    def __init__(self, tg_user):
        self.tg_user = tg_user


class Command(BaseCommand):
    help = 'Start Telegram bot'
    op_buff: Union[OperationBuffer, None] = None
    operation_commands: list = ['/create', '/create_category', '/cancel']
    categories: QuerySet[GoalCategory] | None = None
    goals: QuerySet[Goal] | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # mandatory
        self.tg_client = TgClient(TG_BOT_TOKEN)

    def handle(self, *args, **kwargs):
        offset = 0

        while True:
            response = self.tg_client.get_updates(offset=offset)
            for item in response.result:
                offset = item.update_id + 1
                self.handle_message(item.message)

    def handle_message(self, message):
        tg_user, created = TgUser.objects.get_or_create(
            tg_user_id=message.from_.id,
            defaults={"tg_chat_id": message.chat.id,
                      'username': message.from_.username}
        )
        if created:
            self.tg_client.send_message(chat_id=message.chat.id, text="Greetings!")

        if tg_user.user:
            self.handle_verified_user(message, tg_user)
        else:
            self.handle_unverified_user(message, tg_user)

    def handle_verified_user(self, message, tg_user):

        if '/status' in message.text:
            self.current_status(message)
            return None

        if self.op_buff:
            self.operation_handler(message, tg_user)
            return None

        if not message.text:
            return None

        if '/goals' in message.text:
            self.show_goals(message, tg_user)
        elif '/categories' in message.text:
            self.show_categories(message, tg_user)
        elif '/status' in message.text:
            self.current_status(message)
        elif message.text in self.operation_commands:
            self.op_buff = OperationBuffer(tg_user=tg_user)
            self.operation_handler(message, tg_user)
        else:
            self.tg_client.send_message(chat_id=message.chat.id, text="Doesn't look like anything to me")

    def handle_unverified_user(self, message, tg_user):
        tg_user.generate_verification_code()
        tg_user.save(update_fields=['verification_code'])

        self.tg_client.send_message(
            chat_id=message.chat.id,
            text=f"You're not verified.\n"
                 f'Your verification code:   {tg_user.verification_code}\n'
                 f'Enter this code into corresponding field on the http://skydiario.ml/'
        )

    def operation_handler(self, message, tg_user):
        if '/cancel' in message.text:
            self.cancel_op(message=message)
            return None

        if self.op_buff.current_operation == CurrentOperation.goal_create:
            self.create_goal(message, tg_user)
        elif self.op_buff.current_operation == CurrentOperation.category_create:
            self._create_category(message, tg_user)

        elif message.text == '/create':
            self.create_goal(message, tg_user)
        elif message.text == '/create_category':
            self._create_category(message, tg_user)

        else:
            response = "You're in the middle of something right now \n" \
                       "Finish what you've started or Cancel current operation before proceed.\n" \
                       "Use /cancel command for cancel"
            self.tg_client.send_message(chat_id=message.chat.id, text=response)

    def show_goals(self, message, tg_user) -> str:
        goals_response = self._fetch_goals(tg_user)
        goals = self.goals
        if goals.count() == 0:
            self.goals = None
            self.tg_client.send_message(chat_id=message.chat.id, text='You have no goals here')
        else:
            response = 'Your goals:\n\n' + goals_response
            self.tg_client.send_message(chat_id=message.chat.id, text=response)
            return response

    def show_categories(self, message, tg_user):
        categories_response = self._fetch_categories(tg_user)
        categories = self.categories
        if categories.count() == 0:
            self.categories = None
            self.tg_client.send_message(chat_id=message.chat.id, text='You have no categories')
        else:
            response = 'Available categories:\n\n' + categories_response
            self.tg_client.send_message(chat_id=message.chat.id, text=response)
            return response

    def create_goal(self, message, tg_user):

        self.op_buff.current_operation = CurrentOperation.goal_create
        op_buff = self.op_buff

        if op_buff.operation_state == OperationState.input_required:

            if message.text in op_buff.valid_input and \
                    op_buff.sub_operation == SubOperation.category_id_input:
                op_buff.category_id_input = int(message.text)
                op_buff.sub_operation = SubOperation.title_input
                response = f'You chose category #{op_buff.category_id_input}\n' \
                           f'Enter goal title'
                self.tg_client.send_message(chat_id=message.chat.id, text=response)
                self.op_buff.valid_input = 'Anything'
                return None
            elif op_buff.sub_operation == SubOperation.title_input:
                op_buff.goal_title = message.text
                op_buff.operation_state = OperationState.normal
                self._create_goal(message=message, tg_user=tg_user.user)
                return None
            else:
                response = 'Incorrect. Try again.'
                self.tg_client.send_message(chat_id=message.chat.id, text=response)
                return None

        categories_response = self._fetch_categories(tg_user)
        if self.categories:
            response = 'Chose # of available category:\n\n' + categories_response
            self.tg_client.send_message(chat_id=message.chat.id, text=response)
            op_buff.operation_state = OperationState.input_required
            op_buff.sub_operation = SubOperation.category_id_input
            op_buff.valid_input = [str(cat.id) for cat in self.categories]
        else:
            response = "You have no categories. Create one with \n/create_category command\n" \
                       "Operation cancelled"
            self.op_buff = None
            self.tg_client.send_message(chat_id=message.chat.id, text=response)

    def _create_category(self, message, tg_user):
        response = "Category creation not implemented yet :))\n" \
                   "Operation cancelled"
        self.op_buff = None
        self.tg_client.send_message(chat_id=message.chat.id, text=response)

    def _create_goal(self, message, tg_user):
        category = GoalCategory.objects.filter(
            id=self.op_buff.category_id_input,
            user=tg_user,
            board__participants__role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
            is_deleted=False
        ).first()
        goal = Goal.objects.create(
            user=tg_user, title=self.op_buff.goal_title, category=category
        )
        response = f'Goal "{goal.title}" created successfully'
        self.tg_client.send_message(chat_id=message.chat.id, text=response)
        self.op_buff = None

    def cancel_op(self, message):
        self.op_buff = None
        response = "Dropping all current operations"
        self.tg_client.send_message(chat_id=message.chat.id, text=response)

    def current_status(self, message):
        if self.op_buff:
            response = f'Your current status: \n\n' \
                       f'Operation: {self.op_buff.current_operation[1]}\n' \
                       f'Sub operation: {self.op_buff.sub_operation[1]}\n' \
                       f'Operation state: {self.op_buff.operation_state[1]}\n' \
                       f'Valid input: {self.op_buff.valid_input}'
        else:
            response = 'You have no pending operations'

        self.tg_client.send_message(chat_id=message.chat.id, text=response)

    def _fetch_categories(self, tg_user) -> str:
        categories = GoalCategory.objects.filter(
            user=tg_user.user,
            board__participants__role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
            is_deleted=False
        )

        self.categories = categories

        response = '\n'.join([f'#{category.id} {category.title}' for category in self.categories])
        return response

    def _fetch_goals(self, tg_user) -> str:
        goals = Goal.objects.filter(
            user=tg_user.user,
            status__in=[Goal.Status.to_do, Goal.Status.in_progress, Goal.Status.done]
        )

        self.goals = goals

        response = '\n'.join([f'#{goal.id} {goal.title}' for goal in self.goals])
        return response
