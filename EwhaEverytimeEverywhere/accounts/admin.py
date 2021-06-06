from django.contrib import admin
from django.contrib.auth.models import Permission
from django.utils import timezone
from dateutil.relativedelta import relativedelta  # pip install python-dateutil --upgrade
from .models import Profile, User

# permission 종류가 나옴
admin.site.register(Permission)

class UserDateJoinedFilter(admin.SimpleListFilter):
    title = '유저 가입일'
    parameter_name = 'date_joined_match'

    def lookups(self, request, model_admin):
        candidate = []

        # 현재 월의
        start_date = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        for i in range(6):
            value = '{}-{}'.format(start_date.year, start_date.month)
            label = '{}년 {}월 가입자'.format(start_date.year, start_date.month)
            candidate.append([value, label])
            start_date -= relativedelta(months=1)
        return candidate

    def queryset(self, request, queryset):
        value = self.value()

        if not value:
            return queryset
        try:
            year, month = map(int, value.split('-'))
            queryset = queryset.filter(date_joined__year=year, date_joined__month=month)
        except ValueError:
            return queryset.none()

        return queryset

# auth앱에 있는 User 모델을 그대로 쓴거라면
# from django.contrib.auth.models import User
# admin.site.unregister(User) 해야함, 맨 위에 있는 custom User import 삭제

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'date_joined', 'sex', UserDateJoinedFilter)
    search_fileds = ('username', 'first_name', 'last_name', 'email')
    actions = ['마케팅_이메일보내기']

    def 마케팅_이메일보내기(self, request, queryset):
        for user in queryset:
            pass #알아서 구현해라
        self.message_user(request, 'hello world')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display=['user', 'info']