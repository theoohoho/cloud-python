"""
AWS budget operator

Source: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/budgets.html
"""

import datetime
import re
from dataclasses import asdict, dataclass, field
from typing import Literal, Optional

import boto3


@dataclass
class Notificaiton:
    NotificationType: str = "ACTUAL"
    ComparisonOperator: str = "GREATER_THAN"
    Threshold: float = 0.0
    ThresholdType: str = "PERCENTAGE"
    NotificationState: str = "ALARM"

    def to_dict(self):
        return asdict(self)


@dataclass
class NotificaitonSubscriber:
    SubscriptionType: str = "SNS"
    Address: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class NotificationsWithSubscribers:
    Notification: Notificaiton
    Subscribers: list[NotificaitonSubscriber]

    def to_dict(self):
        return asdict(self)


@dataclass
class CostFilters:
    LinkedAccount: list[str] = field(default_factory=list, repr=False)
    Service: list[str] = field(default_factory=list, repr=False)
    TagKeyValue: list[str] = field(default_factory=list, repr=False)


@dataclass
class CostTypes:
    IncludeCredit: bool


@dataclass
class BudgetLimit:
    Amount: float
    Unit: str = "USD"


@dataclass
class TimePeriod:
    Start: Optional[datetime.datetime] = None
    End: Optional[datetime.datetime] = None


@dataclass
class HistoricalOptions:
    BudgetAdjustmentPeriod: int


@dataclass
class AutoAdjustData:
    AutoAdjustType: Literal["HISTORICAL", "FORECAST"]
    HistoricalOptions: HistoricalOptions


@dataclass
class BudgetCreateUpdate:
    BudgetName: str
    TimeUnit: Literal["DAILY", "MONTHLY", "QUARTERLY", "ANNUALLY"]
    CostFilters: CostFilters
    CostTypes: CostTypes
    BudgetLimit: Optional[BudgetLimit] = None
    TimePeriod: Optional[TimePeriod] = None
    BudgetType: Literal["USAGE", "COST"] = "COST"
    AutoAdjustData: Optional[AutoAdjustData] = None

    def __post_init__(self):
        if self.BudgetLimit is not None and self.AutoAdjustData is not None:
            raise ValueError(
                "Only one of 'BudgetLimit' or 'AutoAdjustData' can be provided"
            )

    def to_dict(self):
        data = asdict(self)
        for k in list(data):
            if not data[k]:
                del data[k]

        if data.get("TimePeriod"):
            if not data["TimePeriod"].get("Start"):
                del data["TimePeriod"]["Start"]
            if not data["TimePeriod"].get("End"):
                del data["TimePeriod"]["End"]

        if data.get("BudgetLimit"):
            data["BudgetLimit"]["Amount"] = str(data["BudgetLimit"]["Amount"])

        for k in list(data["CostFilters"]):
            if not data["CostFilters"][k]:
                del data["CostFilters"][k]

        return data


class AWSBudget:
    def __init__(self, account_id: str):
        self.client = boto3.client("budgets")
        self._account_id = account_id

    def list_budgets(self):
        data = self.client.describe_budgets(Account_id=self._account_id)
        for d in data["Budgets"]:
            notifies = self.client.describe_notifications_for_budget(
                Account_id=self._account_id,
                BudgetName=d["BudgetName"],
            )
            d["Notifications"] = notifies["Notifications"]

        return [d["Budget"] for d in data]

    def get_budget(self, budget_name: str):
        data = self.client.describe_budget(
            Account_id=self._account_id, BudgetName=budget_name
        )
        notifies = self.client.describe_notifications_for_budget(
            Account_id=self._account_id, BudgetName=budget_name
        )
        return data["Budget"], notifies["Notifications"]

    def create_budget(
        self,
        budget_create: BudgetCreateUpdate,
        notifications: list[NotificationsWithSubscribers] = None,
    ):
        self.client.create_budget(
            Account_id=self._account_id,
            Budget=budget_create.to_dict(),
            NotificationsWithSubscribers=[n.to_dict() for n in notifications] or [],
        )

    def update_budget(
        self,
        budget_update: BudgetCreateUpdate,
    ):
        self.client.update_budget(
            Account_id=self._account_id,
            NewBudget=budget_update.to_dict(),
        )

    def delete_budget(self, budget_name: str):
        self.client.delete_budget(Account_id=self._account_id, BudgetName=budget_name)
