from django_filters import FilterSet, CharFilter, ChoiceFilter, IsoDateTimeFromToRangeFilter
from django_filters.widgets import RangeWidget

from .models import certPage

TYPE_CHOICES = (
    (2, '계정 정지'),
    (3, '벌점 부과'),
)


class InfoFilter(FilterSet):
    time = IsoDateTimeFromToRangeFilter(label='탐지날짜',
                                        widget=RangeWidget(attrs={'type': 'datetime-local'}),
                                        )
    type = ChoiceFilter(label='타입', choices=TYPE_CHOICES)
    user = CharFilter(label='접속 계정', lookup_expr='username__icontains') # 외래키 필드의 icontains 쓰려면 이렇게!
    label = CharFilter(label='예상 사용자', lookup_expr='icontains')

    class Meta:
        model = certPage
        fields = ('time', 'mouse_prediction', 'resource_prediction', 'type', 'label', 'user',)

