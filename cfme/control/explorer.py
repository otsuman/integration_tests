# -*- coding: utf-8 -*-
"""Page model for Control / Explorer"""
from functools import partial

from cfme.web_ui.menu import nav

from cfme.control.snmp_form import SNMPForm
from cfme.exceptions import CannotContinueWithNavigation
from cfme.web_ui import fill, flash, form_buttons, table_in_object
from cfme.web_ui import Region, Form, Tree, CheckboxTree, Table, Select, EmailSelectForm, \
    CheckboxSelect, Input, AngularSelect
from cfme.web_ui.multibox import MultiBoxSelect
from selenium.common.exceptions import NoSuchElementException
from utils import version, deferred_verpick
from utils.db import cfmedb
from utils.log import logger
from utils.update import Updateable
from utils.wait import wait_for, TimedOutError
import cfme.fixtures.pytest_selenium as sel
import cfme.web_ui.accordion as accordion
import cfme.web_ui.expression_editor as editor
import cfme.web_ui.toolbar as tb
from utils.pretty import Pretty


events_policies_table = Table(
    table_locator=table_in_object("Assigned to Policies")
)

events_in_policy_table = Table(
    table_locator=table_in_object("Events")
)

cfg_btn = partial(tb.select, "Configuration")


def _ap_single_branch(ugly, nice):
    """generates branch for specific Alert Profile"""
    return [
        lambda ctx: accordion_func(
            "Alert Profiles", "All Alert Profiles", "{} Alert Profiles".format(
                version.pick(nice) if isinstance(nice, dict) else nice),
            ctx["alert_profile_name"])(None),
        {
            "{}_alert_profile_edit".format(ugly):
            lambda _: cfg_btn("Edit this Alert Profile"),

            "{}_alert_profile_assignments".format(ugly):
            lambda _: cfg_btn("Edit assignments for this Alert Profile"),
        }
    ]


def _ap_multi_branch(ugly, nice):
    """Generates branch for listing and adding the profiles"""
    return [
        lambda ctx: accordion_func(
            "Alert Profiles", "All Alert Profiles", "{} Alert Profiles".format(
                version.pick(nice) if isinstance(nice, dict) else nice))(),
        {
            "{}_alert_profile_new".format(ugly):
            lambda _: cfg_btn("Add a New {} Alert Profile".format(
                version.pick(nice) if isinstance(nice, dict) else nice))
        }
    ]


def accordion_func(accordion_title, *nodes):
    """Function to click on the accordion and then on the root node of the underlying tree.

    Automatically handles the "blank page" bug.

    Args:
        accordion_title: Text on accordion.
        *nodes: Nodes to click through.
    """
    def f(_=None):
        try:
            accordion.tree(accordion_title, *nodes)
        except NoSuchElementException:
            raise CannotContinueWithNavigation("blank screen bug!")
    return f


def _policy(item, type_):
    branch = {
        "{}_{}_policy_edit".format(item, type_):
        lambda _: cfg_btn("Edit Basic Info, Scope, and Notes"),

        "{}_{}_policy_conditions".format(item, type_):
        lambda _: cfg_btn("Edit this Policy's Condition assignments"),

        "{}_{}_policy_condition_new".format(item, type_):
        lambda _: cfg_btn("Create a new Condition assigned to this Policy"),

        "{}_{}_policy_event".format(item, type_):
        [
            lambda ctx: events_in_policy_table.click_cell(
                1, ctx["event_name"]
            ),
            {
                "{}_{}_policy_event_actions".format(item, type_):
                lambda _: cfg_btn(
                    "Edit Actions for this Policy Event"
                ),
            }
        ],
    }
    if type_ == "control":
        branch.update({
            "{}_control_policy_events".format(item):
            lambda _: cfg_btn("Edit this Policy's Event assignments"),
        })
    return [
        lambda ctx: accordion_func(
            "Policies", "All Policies", "{} Policies".format(type_.capitalize()),
            "{} {} Policies".format(" ".join(i.capitalize() for i in item.split("_")),
                type_.capitalize()),
            ctx["policy_name"])(None),
        branch
    ]


def _policies(ugly, nice, type_):
    return [
        accordion_func(
            "Policies", "All Policies", "{} Policies".format(type_.capitalize()),
            "{} {} Policies".format(
                " ".join(i.capitalize() for i in ugly.split("_")), type_.capitalize())
        ),
        {
            "{}_{}_policy_new".format(ugly, type_):
            lambda _: cfg_btn("Add a New {} {} Policy".format(
                version.pick(nice) if isinstance(nice, dict) else nice, type_.capitalize()))
        }
    ]


def _condition(ugly, nice):
    return [
        lambda ctx: accordion_func(
            "Conditions", "All Conditions", "{} Conditions".format(
                version.pick(nice) if isinstance(nice, dict) else nice),
            ctx["condition_name"])(None),
        {
            "{}_condition_edit".format(ugly):
            lambda _: cfg_btn("Edit this Condition")
        }
    ]


def _conditions(ugly, nice1, nice2):
    return [
        accordion_func("Conditions", "All Conditions", "{} Conditions".format(
            version.pick(nice1) if isinstance(nice1, dict) else nice1)),
        {
            "{}_condition_new".format(ugly):
            lambda _: cfg_btn("Add a New {} Condition".format(
                version.pick(nice2) if isinstance(nice2, dict) else nice2))
        }
    ]


nav.add_branch(
    "control_explorer",
    {
        "control_explorer_policy_profiles":
        [
            accordion_func("Policy Profiles", "All Policy Profiles"),
            {
                "policy_profile_new":
                lambda _: cfg_btn("Add a New Policy Profile")
            }
        ],

        "policy_profile":
        [
            lambda ctx: accordion_func(
                "Policy Profiles", "All Policy Profiles", ctx["policy_profile_name"])(None),
            {   # None because it normally takes a dummy context and returns a function, therefore()
                "policy_profile_edit": lambda _: cfg_btn("Edit this Policy Profile")
            }
        ],

        "host_compliance_policy": _policy("host", "compliance"),
        "vm_compliance_policy": _policy("vm", "compliance"),
        "replicator_compliance_policy": _policy("replicator", "compliance"),
        "pod_compliance_policy": _policy("pod", "compliance"),
        "container_node_compliance_policy": _policy("container_node", "compliance"),
        "container_image_compliance_policy": _policy("container_image", "compliance"),
        "host_compliance_policies": _policies("host", {
            version.LOWEST: "Host",
            "5.6": "Host / Node"
        }, "compliance"),
        "vm_compliance_policies": _policies("vm", {
            version.LOWEST: "Vm",
            "5.6": "VM and Instance"
        }, "compliance"),
        "replicator_compliance_policies": _policies("replicator", "Replicator", "compliance"),
        "pod_compliance_policies": _policies("pod", "Pod", "compliance"),
        "container_node_compliance_policies": _policies("container_node", "Node", "compliance"),
        "container_image_compliance_policies": _policies("container_image", {
            version.LOWEST: "Image",
            "5.7": "Container Image"
        }, "compliance"),
        "host_control_policy": _policy("host", "control"),
        "vm_control_policy": _policy("vm", "control"),
        "replicator_control_policy": _policy("replicator", "control"),
        "pod_control_policy": _policy("pod", "control"),
        "container_node_control_policy": _policy("container_node", "control"),
        "container_image_control_policy": _policy("container_image", "control"),
        "host_control_policies": _policies("host", {
            version.LOWEST: "Host",
            "5.6": "Host / Node"
        }, "control"),
        "vm_control_policies": _policies("vm", {
            version.LOWEST: "Vm",
            "5.6": "VM and Instance"
        }, "control"),
        "replicator_control_policies": _policies("replicator", "Replicator", "control"),
        "pod_control_policies": _policies("pod", "Pod", "control"),
        "container_node_control_policies": _policies("container_node", "Node", "control"),
        "container_image_control_policies": _policies("container_image", {
            version.LOWEST: "Image",
            "5.7": "Container Image"
        }, "control"),

        "control_explorer_events": accordion_func("Events", "All Events"),

        "control_explorer_event":
        lambda ctx: accordion_func("Events", "All Events", ctx["event_name"])(None),

        "host_condition": _condition("host", "Host"),
        "vm_condition": _condition("vm", {
            version.LOWEST: "All VM and Instance",
            "5.6": "VM and Instance"
        }),
        "replicator_condition": _condition("replicator", "Replicator"),
        "pod_condition": _condition("pod", "Pod"),
        "container_node_condition": _condition("container_node", "Container Node"),
        "container_image_condition": _condition("container_image", "Container Image"),
        "host_conditions": _conditions("host", "Host", {
            version.LOWEST: "Host",
            "5.6": "Host / Node"
        }),
        "vm_conditions": _conditions("vm", {
            version.LOWEST: "All VM and Instance",
            "5.6": "VM and Instance"
        }, "VM"),
        "replicator_conditions": _conditions("replicator", "Replicator", "Replicator"),
        "pod_conditions": _conditions("pod", "Pod", "Pod"),
        "container_node_conditions": _conditions("container_node", "Container Node", "Node"),
        "container_image_conditions": _conditions("container_image", "Container Image", "Image"),

        "control_explorer_action":
        [
            lambda ctx: accordion_func("Actions", "All Actions", ctx["action_name"])(None),
            {
                "control_explorer_action_edit":
                lambda _: cfg_btn("Edit this Action")
            }
        ],

        "control_explorer_actions":
        [
            accordion_func("Actions", "All Actions"),
            {
                "control_explorer_action_new":
                lambda _: cfg_btn("Add a new Action"),
            },
        ],

        "control_explorer_alert":
        [
            lambda ctx: accordion_func("Alerts", "All Alerts", ctx["alert_name"])(None),
            {
                "control_explorer_alert_edit":
                lambda ctx: cfg_btn("Edit this Alert")
            },
        ],

        "control_explorer_alerts":
        [
            accordion_func("Alerts", "All Alerts"),
            {
                "control_explorer_alert_new":
                lambda _: cfg_btn("Add a New Alert"),
            }
        ],

        "vm_instance_alert_profile": _ap_single_branch("vm_instance", "VM and Instance"),
        "vm_instance_alert_profiles": _ap_multi_branch("vm_instance", "VM and Instance"),

        "server_alert_profile": _ap_single_branch("server", "Server"),
        "server_alert_profiles": _ap_multi_branch("server", "Server"),

        "middleware_server_alert_profile": _ap_single_branch(
            "middleware_server", "Middleware Server"),
        "middleware_server_alert_profiles": _ap_multi_branch(
            "middleware_server", "Middleware Server"),

        "provider_alert_profile": _ap_single_branch("provider", "Provider"),
        "provider_alert_profiles": _ap_multi_branch("provider", "Provider"),

        "host_alert_profile": _ap_single_branch("host", {
            version.LOWEST: "Host",
            "5.4": "Host / Node"
        }),
        "host_alert_profiles": _ap_multi_branch("host", {
            version.LOWEST: "Host",
            "5.4": "Host / Node"
        }),
        "datastore_alert_profile": _ap_single_branch("datastore", "Datastore"),
        "datastore_alert_profiles": _ap_multi_branch("datastore", "Datastore"),

        "cluster_alert_profile": _ap_single_branch("cluster", {
            version.LOWEST: "Cluster",
            "5.4": "Cluster / Deployment Role"
        }),
        "cluster_alert_profiles": _ap_multi_branch("cluster", {
            version.LOWEST: "Cluster",
            "5.4": "Cluster / Deployment Role"
        })
    }
)


###################################################################################################
# For checking whether passed condition can be assigned to the policy, some class stuff comes here.
###################################################################################################
class _type_check_object(object):
    """This class is used to check, whether one object can be assigned to another."""
    TYPES = set()

    @classmethod
    def register_type(cls, type):
        cls.TYPES.add(type)
        return type

    def _is_assignable(self, what):
        for klass in _type_check_object.TYPES:
            if isinstance(self, klass):
                return True
        else:
            return False


@_type_check_object.register_type
class HostObject(_type_check_object):
    pass


@_type_check_object.register_type
class VMObject(_type_check_object):
    pass


@_type_check_object.register_type
class ReplicatorObject(_type_check_object):
    pass


@_type_check_object.register_type
class PodObject(_type_check_object):
    pass


@_type_check_object.register_type
class ContainerNodeObject(_type_check_object):
    pass


@_type_check_object.register_type
class ContainerImageObject(_type_check_object):
    pass


def click_if_displayed(loc):
    try:
        wait_for(lambda: sel.is_displayed(loc), num_sec=2, delay=0.2)
        sel.click(loc)
    except TimedOutError:
        pass


class BaseCondition(Updateable, Pretty):
    """Base class for conditions.

    They differ just with the navigation prefix, so that is the self.PREFIX which gets changed.

    Usage:
        >> cond = HostCondition("mycond",         # or VMCondition
        ..     expression="fill_count(Host.VMs, >, 50)",
        ..     scope="fill_count(Host.Files, >, 150)")
        >> cond.create()
        >> with update(cond):
        ..     cond.notes = "Important!"
        >> cond.delete()

    Args:
        description: Name of the condition.
        notes: Notes.
        scope: Program, setting the Scope of the Condition.
        expression: Program, setting the Scope of the Expression.
    """
    PREFIX = None
    DELETE_STRING = None

    form = Form(
        fields=[
            ("description", Input("description")),
            ("notes", "textarea#notes"),
            ("scope", editor.Expression(
                lambda: click_if_displayed(
                    "//img[@alt='Edit this Scope']"))),
            ("expression", editor.Expression(
                lambda: click_if_displayed(
                    "//img[@alt='Edit this Expression']"))),
        ]
    )
    pretty_attrs = ['description', 'expression', 'scope']

    def __init__(self,
                 description,
                 notes=None,
                 scope=None,
                 expression=None):
        if not self.PREFIX:
            raise NotImplementedError("You must use an inherited class from {}".format(
                type(self).__name__))
        self.description = description
        self.notes = notes
        self.scope = scope
        self.expression = expression

    @property
    def exists(self):
        conditions = cfmedb()["conditions"]
        return cfmedb().session\
            .query(conditions.description)\
            .filter(conditions.description == self.description)\
            .count() > 0

    def create(self, cancel=False):
        """Creates new Condition according to the informations filed in constructor.

        Args:
            cancel: Whether to cancel the process instead of saving.
        """
        sel.force_navigate(self.PREFIX + "condition_new")
        fill(self.form, self.__dict__, action=form_buttons.cancel if cancel else form_buttons.add)
        flash.assert_no_errors()

    def update(self, updates):
        """Updates the informations in the object and then updates the Condition in CFME.

        Args:
            updates: Provided by update() context manager.
        """
        sel.force_navigate(self.PREFIX + "condition_edit",
                           context=dict(condition_name=self.description))
        fill(self.form, updates, action=form_buttons.save)
        flash.assert_no_errors()

    def delete(self, cancel=False):
        """Deletes the condition in CFME.

        Args:
            cancel: Whether to cancel the process instead of saving.
        """
        sel.force_navigate(self.PREFIX + "condition",
                           context=dict(condition_name=self.description))
        cfg_btn(self.DELETE_STRING, invokes_alert=True)
        sel.handle_alert(cancel)
        flash.assert_no_errors()


class HostCondition(BaseCondition, HostObject):
    PREFIX = "host_"
    PRETTY_NAME = "Host / Node"
    DELETE_STRING = deferred_verpick({
        version.LOWEST: "Delete this Host Condition",
        '5.4': "Delete this Host / Node Condition"
    })


class VMCondition(BaseCondition, VMObject):
    PREFIX = "vm_"
    PRETTY_NAME = "VM and Instance"
    DELETE_STRING = "Delete this VM and Instance Condition"


class ReplicatorCondition(BaseCondition, ReplicatorObject):
    PREFIX = "replicator_"
    PRETTY_NAME = "Replicator"
    DELETE_STRING = "Delete this Replicator Condition"


class PodCondition(BaseCondition, PodObject):
    PREFIX = "pod_"
    PRETTY_NAME = "Pod"
    DELETE_STRING = "Delete this Pod Condition"


class ContainerNodeCondition(BaseCondition, ContainerNodeObject):
    PREFIX = "container_node_"
    PRETTY_NAME = "Node"
    DELETE_STRING = "Delete this Node Condition"


class ContainerImageCondition(BaseCondition, ContainerImageObject):
    PREFIX = "container_image_"
    PRETTY_NAME = "Image"
    DELETE_STRING = deferred_verpick({
        version.LOWEST: "Delete this Image Condition",
        '5.7': "Delete this Container Image Condition"
    })


class BasePolicy(Updateable, Pretty):
    PREFIX = None
    DELETE_STRING = None

    assigned_conditions = Table(
        table_locator=table_in_object("Conditions")
    )

    assigned_events = Table(
        table_locator=table_in_object("Events")
    )

    form = Form(
        fields=[
            ("description", Input("description")),
            ("active", Input("active")),
            ("scope", editor.Expression()),
            ("notes", "textarea#notes"),
        ]
    )

    conditions = MultiBoxSelect.default()

    # Event action assignment
    event_actions = Form(
        fields=[
            (
                "true",
                MultiBoxSelect(
                    "select#choices_chosen_true",
                    "select#members_chosen_true",
                    "//a[contains(@href, 'true')]/img[contains(@alt, 'Remove selected')]",
                    "//a[contains(@href, 'true')]/img[contains(@alt, 'Move selected')]",
                    remove_all="//a[contains(@href, 'true')]/img[contains(@alt, 'Remove all')]",
                    async="//a[contains(@href, 'true')]"
                    "/img[contains(@alt, 'Set selected Actions to Asynchronous')]",
                    sync="//a[contains(@href, 'true')]"
                    "/img[contains(@alt, 'Set selected Actions to Synchronous')]",
                )
            ),
            (
                "false",
                MultiBoxSelect(
                    "select#choices_chosen_false",
                    "select#members_chosen_false",
                    "//a[contains(@href, 'false')]/img[contains(@alt, 'Remove selected')]",
                    "//a[contains(@href, 'false')]/img[contains(@alt, 'Move selected')]",
                    remove_all="//a[contains(@href, 'false')]/img[contains(@alt, 'Remove all')]",
                    async="//a[contains(@href, 'false')]"
                    "/img[contains(@alt, 'Set selected Actions to Asynchronous')]",
                    sync="//a[contains(@href, 'false')]"
                    "/img[contains(@alt, 'Set selected Actions to Synchronous')]",
                )
            ),
        ]
    )
    pretty_attrs = ['description', 'scope']

    def __init__(self,
                 description,
                 active=True,
                 notes=None,
                 scope=None):
        if not self.PREFIX:
            raise NotImplementedError("You must use an inherited class from {}".format(
                type(self).__name__))
        self.description = description
        self.notes = notes
        self.active = active
        self.scope = scope

    @property
    def exists(self):
        policies = cfmedb()["miq_policies"]
        return cfmedb().session\
            .query(policies.description)\
            .filter(policies.description == self.description)\
            .count() > 0

    @property
    def _on_detail_page(self):
        raise NotImplementedError("You must implement this in inherited class")

    def create(self, cancel=False):
        """Creates new Condition according to the informations filed in constructor.

        Args:
            cancel: Whether to cancel the process instead of saving.
        """
        sel.force_navigate(self.PREFIX + "policy_new")
        fill(
            self.form,
            self.__dict__,
            action=form_buttons.cancel if cancel else form_buttons.add)
        flash.assert_no_errors()

    def copy(self, cancel=False):
        """Copy this Policy from CFME.

        Args:
            cancel: Whether to cancel the process instead of copying.
        """
        sel.force_navigate(self.PREFIX + "policy",
                           context={"policy_name": self.description})
        cfg_btn(self.COPY_STRING, invokes_alert=True)
        sel.handle_alert(cancel)
        flash.assert_no_errors()
        new_description = "Copy of {}".format(self.description)
        return type(self)(new_description)

    def update(self, updates):
        """Updates the informations in the object and then updates the Condition in CFME.

        Args:
            updates: Provided by update() context manager.
        """
        sel.force_navigate(self.PREFIX + "policy_edit",
                           context=dict(policy_name=self.description))
        fill(self.form, updates, action=form_buttons.save)
        flash.assert_no_errors()

    def delete(self, cancel=False):
        """Deletes the condition in CFME.

        Args:
            cancel: Whether to cancel the process instead of saving.
        """
        sel.force_navigate(self.PREFIX + "policy", context=dict(policy_name=self.description))
        cfg_btn(self.DELETE_STRING, invokes_alert=True)
        sel.handle_alert(cancel)
        flash.assert_no_errors()

    def assign_conditions(self, *conditions):
        """Assign one or more conditions to this Policy.

        If using the :py:class:`BaseCondition` assignment, you must provide a correct type of
        condition (you cannot assign eg. :py:class:`VMCondition` to :py:class:`HostControlPolicy`).

        Args:
            *conditions: Each condition can be either :py:class:`str` or :py:class:`BaseCondition`
                instance.
        """
        assign_names = []
        for condition in conditions:
            if isinstance(condition, BaseCondition):
                if not self._is_assignable(condition):
                    raise TypeError("You cannot add VM object to Host and vice versa!")
                # Assign condition.description
                logger.debug(
                    "Assigning condition `%s` to policy `%s`",
                    condition.description, self.description)
                if not condition.exists:
                    condition.create()
                assign_names.append(condition.description)
            elif isinstance(condition, basestring):
                # assign condition
                logger.debug(
                    "Assigning condition `%s` to policy `%s`", condition, self.description)
                assign_names.append(condition)
            else:
                raise TypeError("assign_conditions() accepts only BaseCondition and basestring")
        sel.force_navigate(self.PREFIX + "policy_conditions",
                           context=dict(policy_name=self.description))
        fill(self.conditions, assign_names)
        form_buttons.save()
        flash.assert_no_errors()
        return self

    def is_condition_assigned(self, condition):
        """Check whether the provided condition is assigned to the Policy.

        Args:
            condition: Condition to check. Can be either :py:class:`str` or the
                :py:class:`BaseCondition` object.
        Returns: :py:class:`bool` - `True` if present, `False` if not.
        """
        if isinstance(condition, basestring):
            condition_name = condition
        elif isinstance(condition, BaseCondition):
            if not self._is_assignable(condition):
                return False  # Cannot be, obviously ...
            condition_name = condition.description
        else:
            raise TypeError("is_condition_assigned accepts string or BaseCondition object only!")
        sel.force_navigate(self.PREFIX + "policy",
                           context=dict(policy_name=self.description))
        try:
            sel.move_to_element(self.assigned_conditions)
            return bool(self.assigned_conditions.find_cell("description", condition_name))
        except NoSuchElementException:
            return False

    def is_event_assigned(self, event):
        """Check whether the provided event is assigned to the Policy.

        Args:
            event: Event to check. :py:class:`str`.

        Returns: :py:class:`bool` - `True` if present, `False` if not.
        """
        sel.force_navigate(self.PREFIX + "policy",
                           context=dict(policy_name=self.description))
        try:
            sel.move_to_element(self.assigned_events)
            return bool(self.assigned_events.find_cell("description", event))
        except NoSuchElementException:
            return False

    def assign_actions_to_event(self, event, actions):
        """This method takes a list or dict of actions, goes into the policy event and assigns them.

        Actions can be passed both as the objects, but they can be passed also as a string.
        Actions, passed as an object but not created yet, will be created.
        If the specified event is not assigned to the policy, it will be assigned.

        Args:
            event: Name of the event under which the actions will be assigned.
            actions: If :py:class:`list` (or similar), all of these actions will be set under
                TRUE section. If :py:class:`dict`, the action is key and value specifies its
                placement. If it's True, then it will be put in the TRUE section and so on.

        """
        true, false = [], []
        if isinstance(actions, Action):
            true.append(actions)
        elif isinstance(actions, list) or isinstance(actions, tuple) or isinstance(actions, set):
            true.extend(actions)
        elif isinstance(actions, dict):
            for action, is_true in actions.iteritems():
                if is_true:
                    true.append(action)
                else:
                    false.append(action)
        else:
            raise TypeError("assign_actions_to_event expects, list, tuple, set or dict!")
        # Check whether actions exist
        for action in true + false:
            if isinstance(action, Action):
                if not action.exists:
                    action.create()
                    assert action.exists, "Could not create action {}!".format(action.description)
            else:  # string
                if not Action(action, "Tag").exists:
                    raise NameError("Action with name {} does not exist!".format(action))
        # Check whether we have all necessary events assigned
        if not self.is_event_assigned(event):
            self.assign_events(event, do_not_uncheck=True)
            assert self.is_event_assigned(event), "Could not assign event {}!".format(event)
        # And now we can assign actions
        sel.force_navigate(self.PREFIX + "policy_event_actions",
                           context=dict(policy_name=self.description, event_name=event))
        fill(
            self.event_actions,
            dict(
                true=[str(action) for action in true],
                false=[str(action) for action in false],
            )
        )
        form_buttons.save()
        flash.assert_no_errors()


class BaseControlPolicy(BasePolicy):
    events = CheckboxSelect("//div[@id='policy_info_div']")

    def assign_events(self, *events, **kwargs):
        """(un)Assign one or more events to this Policy.

        Args:
            *events: Each event is represented by :py:class:`str`. If it is present, it will be
                checked. If it is not present, it will be unchecked.
        Keywords:
            do_not_uncheck: If specified and True, no unchecking will happen.
        """
        sel.force_navigate(self.PREFIX + "policy_events",
                           context=dict(policy_name=self.description))
        if not kwargs.get("do_not_uncheck", False):
            fill(self.events, False)
        fill(self.events, {sel.ByText(event) for event in events})
        form_buttons.save()
        flash.assert_no_errors()


class HostCompliancePolicy(BasePolicy, HostObject):
    PREFIX = "host_compliance_"

    DELETE_STRING = deferred_verpick({
        version.LOWEST: "Delete this Host Policy",
        "5.4": "Delete this Host / Node Policy"
    })

    COPY_STRING = deferred_verpick({
        version.LOWEST: "Copy this Host Policy",
        "5.4": "Copy this Host / Node Policy"
    })

    def __str__(self):
        if version.current_version() >= "5.4":
            return "Host / Node Compliance: {}".format(self.description)
        else:
            return "Host Compliance: {}".format(self.description)


class VMCompliancePolicy(BasePolicy, VMObject):
    PREFIX = "vm_compliance_"
    DELETE_STRING = "Delete this VM and Instance Policy"
    COPY_STRING = "Copy this VM and Instance Policy"

    def __str__(self):
        return "VM and Instance Compliance: {}".format(self.description)


class ReplicatorCompliancePolicy(BasePolicy, ReplicatorObject):
    PREFIX = "replicator_compliance_"
    DELETE_STRING = "Delete this Replicator Policy"
    COPY_STRING = "Copy this Replicator Policy"

    def __str__(self):
        return "Replcaitor Compliance: {}".format(self.description)


class PodCompliancePolicy(BasePolicy, PodObject):
    PREFIX = "pod_compliance_"
    DELETE_STRING = "Delete this Pod Policy"
    COPY_STRING = "Copy this Pod Policy"

    def __str__(self):
        return "Pod Compliance: {}".format(self.description)


class ContainerNodeCompliancePolicy(BasePolicy, ContainerNodeObject):
    PREFIX = "container_node_compliance_"
    DELETE_STRING = "Delete this Node Policy"
    COPY_STRING = "Copy this Node Policy"

    def __str__(self):
        return "Container Node Compliance: {}".format(self.description)


class ContainerImageCompliancePolicy(BasePolicy, ContainerImageObject):
    PREFIX = "container_image_compliance_"
    DELETE_STRING = deferred_verpick({
        version.LOWEST: "Delete this Image Policy",
        "5.7": "Delete this Container Image Policy"
    })
    COPY_STRING = deferred_verpick({
        version.LOWEST: "Copy this Image Policy",
        "5.7": "Copy this Container Image Policy"
    })

    def __str__(self):
        return "Container Image Compliance: {}".format(self.description)


class HostControlPolicy(BaseControlPolicy, HostObject):
    PREFIX = "host_control_"

    DELETE_STRING = deferred_verpick({
        version.LOWEST: "Delete this Host Policy",
        "5.4": "Delete this Host / Node Policy"
    })

    COPY_STRING = deferred_verpick({
        version.LOWEST: "Copy this Host Policy",
        "5.4": "Copy this Host / Node Policy"
    })

    def __str__(self):
        if version.current_version() >= "5.4":
            return "Host / Node Control: {}".format(self.description)
        else:
            return "Host Control: {}".format(self.description)


class VMControlPolicy(BaseControlPolicy, VMObject):
    PREFIX = "vm_control_"
    DELETE_STRING = "Delete this VM and Instance Policy"
    COPY_STRING = "Copy this VM and Instance Policy"

    def __str__(self):
        return "VM and Instance Control: {}".format(self.description)


class ReplicatorControlPolicy(BaseControlPolicy, ReplicatorObject):
    PREFIX = "replicator_control_"
    DELETE_STRING = "Delete this Replicator Policy"
    COPY_STRING = "Copy this Replicator Policy"

    def __str__(self):
        return "Replcaitor Control: {}".format(self.description)


class PodControlPolicy(BaseControlPolicy, PodObject):
    PREFIX = "pod_control_"
    DELETE_STRING = "Delete this Pod Policy"
    COPY_STRING = "Copy this Pod Policy"

    def __str__(self):
        return "Pod Control: {}".format(self.description)


class ContainerNodeControlPolicy(BaseControlPolicy, ContainerNodeObject):
    PREFIX = "container_node_control_"
    DELETE_STRING = "Delete this Node Policy"
    COPY_STRING = "Copy this Node Policy"

    def __str__(self):
        return "Container Node Control: {}".format(self.description)


class ContainerImageControlPolicy(BaseControlPolicy, ContainerImageObject):
    PREFIX = "container_image_control_"
    DELETE_STRING = deferred_verpick({
        version.LOWEST: "Delete this Image Policy",
        "5.7": "Delete this Container Image Policy"
    })
    COPY_STRING = deferred_verpick({
        version.LOWEST: "Copy this Image Policy",
        "5.7": "Copy this Container Image Policy"
    })

    def __str__(self):
        return "Container Image Control: {}".format(self.description)


class Alert(Updateable, Pretty):
    """Alert representation object.

    Example:

        >>> alert = Alert("my_alert", timeline_event=True, driving_event="Hourly Timer")
        >>> alert.create()
        >>> alert.delete()

    Args:
        description: Name of the Alert.
        based_on: Cluster, Datastore, Host, Provider, ...
        evaluate: If specified as :py:class:`str`, it will select 'Expression (Custom)' and compile
            the string into the program which selects the expression. If specified as callable
            (something that has ``.__call__`` method inside), then it will also select the custom
            expression and will use the function to fill the expression. If specified as tuple(list)
            it will use it as follows: ``("What to Evaluate selection", dict(values="for form"))``.
            If you want to select Nothing, you will therefore pass ``("Nothing", {})``.

            Other example:
                .. code-block:: python

                    ("Hardware Reconfigured",
                     dict(hw_attribute="Number of CPUs", hw_attribute_operator="Increased")
                    )

            For all fields, check the `form` class variable.
        driving_event: This Alert's driving event (Hourly Timer, ...).
        notification_frequency: 1 Minute, 2 Minutes, ...
        snmp_trap: Values for :py:class:`cfme.web_ui.snmp_form.SNMPForm`. If `False`, it is disabled
        emails: Whether to send e-mails. `False` disables, string or list of strings
            with emails enables.
        timeline_event: Whether generate a timeline event.
        mgmt_event: If specified as string, it will reveal teh form and types it into the text box.
            If False, then it will be disabled. None - don't care.

    Note:
        If you don't specify the 'master' option or set it False (like snmp_trap for
        snmp_trap_hosts), the dependent variables will be None'd to ensure that things like
        :py:class:`NoSuchElementException` do not happen.
    """
    form = Form(
        fields=[
            ("description", Input("description")),
            ("active", Input("enabled_cb")),
            ("based_on", {
                version.LOWEST: Select("select#miq_alert_db"),
                "5.5": AngularSelect("miq_alert_db", exact=True)}),
            ("evaluate", {
                version.LOWEST: Select("select#exp_name"),
                "5.5": AngularSelect("exp_name")}),
            ("driving_event", {
                version.LOWEST: Select("select#exp_event"),
                "5.5": AngularSelect("exp_event")}),
            ("notification_frequency", {
                version.LOWEST: Select("select#repeat_time"),
                "5.5": AngularSelect("repeat_time")}),
            # Different evaluations begin
            # Event log threshold
            ("event_log_message_type", {
                version.LOWEST: Select("select#select_event_log_message_filter_type"),
                "5.5": AngularSelect("select_event_log_message_filter_type")}),
            ("event_log_message_value", Input("event_log_message_filter_value")),
            ("event_log_name", Input("event_log_name")),
            ("event_log_level", Input("event_log_level")),
            ("event_log_event_id", Input("event_log_event_id")),
            ("event_log_source", Input("event_log_source")),
            ("event_time_threshold", {
                version.LOWEST: Select("select#time_threshold"),
                "5.5": AngularSelect("time_threshold")}),  # shared
            ("event_count_threshold", Input("freq_threshold")),  # shared
            # Event threshold (uses the shared fields from preceeding section)
            ("event_type", {
                version.LOWEST: Select("select#event_types"),
                "5.5": AngularSelect("event_types")}),
            # HW reconfigured + VM Value Changed
            ("hw_attribute", {
                version.LOWEST: Select("select#select_hdw_attr"),
                "5.5": AngularSelect("select_hdw_attr")}),
            ("hw_attribute_operator", {
                version.LOWEST: Select("select#select_operator"),
                "5.5": AngularSelect("select_operator")}),
            # Normal operating range
            ("performance_field", {
                version.LOWEST: Select("select#perf_column"),
                "5.5": AngularSelect("perf_column")}),
            ("performance_field_operator", {
                version.LOWEST: Select("select#select_operator"),
                "5.5": AngularSelect("select_operator")}),
            ("performance_time_threshold", {
                version.LOWEST: Select("select#rt_time_threshold"),
                "5.5": AngularSelect("rt_time_threshold")}),
            # Real Time Performance (uses fields from previous)
            ("performance_field_value", Input("value_threshold")),
            ("performance_trend", {
                version.LOWEST: Select("select#trend_direction"),
                "5.5": AngularSelect("trend_direction")}),
            ("performance_debug_trace", {
                version.LOWEST: Select("select#debug_trace"),
                "5.5": AngularSelect("debug_trace")}),
            # VMWare alarm
            ("vmware_alarm_provider", {
                version.LOWEST: Select("select#select_ems_id"),
                "5.5": AngularSelect("select_ems_id")}),
            ("vmware_alarm_type", {
                version.LOWEST: Select("select#select_ems_alarm_mor"),
                "5.5": AngularSelect("select_ems_alarm_mor")}),
            # Different evaluations end
            ("send_email", Input("send_email_cb")),
            ("emails", EmailSelectForm()),
            ("snmp_trap_send", Input("send_snmp_cb")),
            ("snmp_trap", SNMPForm()),
            ("timeline_event", Input("send_evm_event_cb")),
            ("mgmt_event_send", Input("send_event_cb")),
            ("mgmt_event", Input("event_name")),
        ]
    )

    pretty_attrs = ['description', 'evaluate']

    def __init__(self,
                 description,
                 active=None,
                 based_on=None,
                 evaluate=None,
                 driving_event=None,
                 notification_frequency=None,
                 snmp_trap=None,
                 emails=None,
                 timeline_event=None,
                 mgmt_event=None):
        self.description = description
        self.active = active
        self.based_on = based_on
        self.evaluate = evaluate
        self.driving_event = driving_event
        self.notification_frequency = notification_frequency
        self.snmp_trap = snmp_trap
        self.emails = emails
        self.timeline_event = timeline_event
        self.mgmt_event = mgmt_event

    def __str__(self):
        """Conversion to string used when assigning in multibox selector."""
        return self.description

    @property
    def exists(self):
        alerts = cfmedb()["miq_alerts"]
        return cfmedb().session\
            .query(alerts.description)\
            .filter(alerts.description == self.description)\
            .count() > 0

    def create(self, cancel=False):
        sel.force_navigate("control_explorer_alert_new")
        self._fill()
        if cancel:
            form_buttons.cancel()
        else:
            form_buttons.add()
        flash.assert_no_errors()

    def copy(self, cancel=False):
        """Copy this Alert from CFME.

        Args:
            cancel: Whether to cancel the copying (default False).
        """
        sel.force_navigate("control_explorer_alert", context={"alert_name": self.description})
        cfg_btn("Copy this Alert", invokes_alert=True)
        sel.handle_alert(cancel)
        new_description = "{}_copy".format(self.description)
        fill(self.form, {"description": new_description})
        if cancel:
            form_buttons.cancel()
        else:
            form_buttons.add()
        flash.assert_no_errors()
        return Alert(new_description)

    def update(self, updates, cancel=False):
        """Update the object with new values and save.

        Args:
            updates: Provided by update() context manager.
            cancel: Whether to cancel the update (default False).
        """
        for key, value in updates.iteritems():
            if key in {"self", "cancel"}:
                continue
            try:
                getattr(self, key)
                if value is not None:
                    setattr(self, key, value)
            except AttributeError:
                pass
        # Go update!
        sel.force_navigate("control_explorer_alert_edit",
                           context={"alert_name": self.description})
        self._fill()
        if cancel:
            form_buttons.cancel()
        else:
            form_buttons.save()
        flash.assert_no_errors()

    def delete(self, cancel=False):
        """Delete this Alert from CFME.

        Args:
            cancel: Whether to cancel the deletion (default False).
        """
        sel.force_navigate("control_explorer_alert", context={"alert_name": self.description})
        cfg_btn("Delete this Alert", invokes_alert=True)
        sel.handle_alert(cancel)
        flash.assert_no_errors()

    def _fill(self):
        """This function prepares the values and fills the form."""
        fill_details = dict(
            description=self.description,
            active=self.active,
            based_on=self.based_on,
            driving_event=self.driving_event,
            notification_frequency=self.notification_frequency,
            timeline_event=self.timeline_event,
        )
        # Hideable sections:
        if self.snmp_trap is not None:
            # We have to check or uncheck the checkbox and then subsequently handle the form fill
            if self.snmp_trap is False:
                fill_details["snmp_trap_send"] = False
                fill_details["snmp_trap"] = None
            else:
                fill_details["snmp_trap_send"] = True
                fill_details["snmp_trap"] = self.snmp_trap
        if self.emails is not None:
            # We have to check or uncheck the checkbox and then subsequently handle the form fill
            if self.emails is False:
                fill_details["send_email"] = False
                fill_details["emails"] = None
            else:
                fill_details["send_email"] = True
                fill_details["emails"] = self.emails
        if self.mgmt_event is not None:
            # We have to check or uncheck the checkbox and then subsequently handle the form fill
            if self.mgmt_event is False:
                fill_details["mgmt_event_send"] = False
                fill_details["mgmt_event"] = None
            else:
                fill_details["mgmt_event_send"] = True
                fill_details["mgmt_event"] = self.mgmt_event
        # Evaluate expression
        form_func = lambda: None
        if self.evaluate:
            if isinstance(self.evaluate, basestring):
                # String -> compile program
                fill_details["evaluate"] = "Expression (Custom)"
                form_func = editor.create_program(self.evaluate)
            elif hasattr(self.evaluate, "__call__"):
                # Callable
                fill_details["evaluate"] = "Expression (Custom)"
                form_func = self.evaluate
            elif isinstance(self.evaluate, tuple) or isinstance(self.evaluate, list):
                # Tuple -> dropdown select + the values in the form which will appear
                assert len(self.evaluate) == 2, "evaluate must have length of 2"
                fill_details["evaluate"], evaluate_values = self.evaluate
                assert isinstance(evaluate_values, dict), "The values for evaluate must be dict!"
                fill_details.update(evaluate_values)
            else:
                raise TypeError("evaluate must be either string with dropdown value or function "
                                "or a 2-tuple with (dropdown value, dict of values to set)")
        fill(self.form, fill_details)
        form_func()     # Fill the expression if present


class Action(Updateable, Pretty):
    """This class represents one Action.

    Example:

        >>> from cfme.control.explorer import Action
        >>> action = Action("some_action",
        ...     "Tag", dict(tag=("My Company Tags", "Department", "Accounting")))
        >>> action.create()
        >>> action.delete()

    Args:
        description: Action name.
        action_type: Type of the action, value from the dropdown select.
        action_values: :py:class:`dict` with values to give to the sub-form (in Actions.forms).
            See the dictionary for further details. If you fill the `Tag` section, you have to pass
            the tuple or list with parameters for :py:meth:`Tree.click_path` for Tag selection.
            For `Evaluate Alerts`, you have to pass an iterable with list of alerts to select.

    """
    form = Form(
        fields=[
            ("description", Input("description")),
            ("action_type", AngularSelect("miq_action_type", exact=True)),
            # Evaluate Alerts (TODO)
        ]
    )

    trees = '|'.join([
        "//div[@id='action_tags_treebox']/div/table",   # Old builds
        "//div[@id='action_tags_treebox']/ul",          # New builds
    ])

    sub_forms = {
        "Assign Profile to Analysis Task":
        Form(
            fields=[
                ("analysis_profile", AngularSelect("analysis_profile", exact=True)),
            ]
        ),

        "Create a Snapshot":
        Form(
            fields=[
                ("snapshot_name", Input("snapshot_name")),
            ]
        ),

        "Delete Snapshots by Age":
        Form(
            fields=[
                ("snapshot_age", AngularSelect("snapshot_age")),
            ]
        ),

        "Inherit Parent Tags":
        Form(
            fields=[
                ("parent_type", AngularSelect("parent_type")),
                ("tags", CheckboxSelect({
                    version.LOWEST:
                    "//*[@id='action_options_div']/fieldset/table/tbody/tr[2]/td[2]/table",
                    "5.5": "//label[normalize-space(.)='Categories']/../div/table/tbody"})),
            ]
        ),

        "Invoke a Custom Automation":
        Form(
            fields=[
                ("message", Input("object_message")),
                ("request", Input("object_request")),
                ("attribute_1", Input("attribute_1")),
                ("value_1", Input("value_1")),
                ("attribute_2", Input("attribute_2")),
                ("value_2", Input("value_2")),
                ("attribute_3", Input("attribute_3")),
                ("value_3", Input("value_3")),
                ("attribute_4", Input("attribute_4")),
                ("value_4", Input("value_4")),
                ("attribute_5", Input("attribute_5")),
                ("value_5", Input("value_5")),
            ]
        ),

        "Reconfigure CPUs":
        Form(
            fields=[
                ("num_cpus", AngularSelect("cpu_value")),
            ]
        ),

        "Reconfigure Memory":
        Form(
            fields=[
                ("memory_size", Input("memory_value")),
            ]
        ),

        "Remove Tags":
        CheckboxSelect({
            version.LOWEST: "//div[@id='action_options_div']//td[@class='key' and "
                            "normalize-space(.)='Categories']/../td/table/tbody",
            "5.5": "//label[normalize-space(.)='Categories']/../div/table/tbody",
        }),

        "Send an E-mail":
        Form(
            fields=[
                ("from", Input("from")),
                ("to", Input("to")),
            ]
        ),

        "Set a Custom Attribute in vCenter":
        Form(
            fields=[
                ("attribute", Input("attribute")),
                ("value", Input("value")),
            ]
        ),

        "Send an SNMP Trap":
        SNMPForm(),

        "Tag":
        Form(
            fields=[
                (
                    "tag",
                    Tree(trees)
                ),
            ]
        ),

        "Evaluate Alerts": MultiBoxSelect.default()
    }

    pretty_attrs = ['description', 'action_type', 'action_values']

    def __init__(self, description, action_type, action_values=None):
        assert action_type in self.sub_forms.keys(), "Unrecognized Action Type ({})".format(
            action_type)
        self.description = description
        self.action_type = action_type
        self.action_values = action_values or self._default_values

    def __str__(self):
        return self.description

    @property
    def exists(self):
        actions = cfmedb()["miq_actions"]
        return cfmedb().session\
            .query(actions.description)\
            .filter(actions.description == self.description)\
            .count() > 0

    @property
    def _default_values(self):
        """This property provides a default value depending on action_type."""
        if self.action_type == "Tag":
            return tuple()
        else:
            return dict()

    def _fill(self, action):
        """This method handles filling of the form. Handles differences between some types
        of forms."""
        fill(self.form, dict(description=self.description, action_type=self.action_type))
        if self.sub_forms[self.action_type] is not None:
            fill(self.sub_forms[self.action_type], self.action_values)
            action()
            flash.assert_no_errors()
        else:
            raise Exception("You must specify action_type!")

    def create(self, cancel=False):
        """Create this Action in UI.

        Args:
            cancel: Whether to cancel the creation (default False).
        """
        sel.force_navigate("control_explorer_action_new")
        action = form_buttons.cancel if cancel else form_buttons.add
        return self._fill(action)

    def update(self, updates, cancel=False):
        """Update this Action in UI.

        Args:
            updates: Provided by update() context manager.
            cancel: Whether to cancel the update (default False).
        """
        sel.force_navigate("control_explorer_action_edit",
                           context={"action_name": self.description})
        action = form_buttons.cancel if cancel else form_buttons.save
        if "description" in updates:
            self.description = updates["description"]

        if "action_type" in updates and updates["action_type"] != self.action_type:
            action_type = updates["action_type"]
            logger.debug("Changing action_type for Action %s", self.description)
            assert action_type in self.sub_forms.keys(), "Unk. Action Type ({})".format(action_type)
            self.action_type = action_type
            self.action_values = self._default_values
        if "action_values" in updates:
            if isinstance(self.action_values, dict):
                self.action_values.update(updates["action_values"])
            else:
                # tuple or list for Tag selector
                self.action_values = updates["action_values"]

        return self._fill(action)

    def delete(self, cancel=False):
        """Delete this Action in UI.

        Args:
            cancel: Whether to cancel the deletion (default False).
        """
        sel.force_navigate("control_explorer_action",
                           context={"action_name": self.description})
        cfg_btn("Delete this Action", invokes_alert=True)
        sel.handle_alert(cancel)
        flash.assert_no_errors()


class PolicyProfile(Updateable, Pretty):
    """This class represents a Policy Profile.

    Policies can be assigned to Policy Profile and also the Policy Profile.

    Example:

        >> from cfme.control.explorer import PolicyProfile, HostControlPolicy, VMCompliancePolicy
        >> profile = PolicyProfile("some_profile",
        ..     policies=[HostControlPolicy("funny"), VMCompliancePolicy("things")])
        >> profile.create()
        >> with update(profile):
        ..     profile.notes = "notes!"
        >> profile.delete()

    Args:
        description: Name of the Alert Profile.
        policies: Iterable with policies. Can be of :py:class:`str` but also objects of
            :py:class:`BasePolicy` can be used, then Policy Profile checks for presence of policies
            and if they aren't created yet, it will create them.
        notes: Notes for the Policy Profile.
    """
    form = Form(
        fields=[
            ("description", Input("description")),
            ("notes", "textarea#notes"),
            ("policies", MultiBoxSelect.default())
        ]
    )

    pretty_attrs = ['description', 'policies']

    def __init__(self, description, policies=None, notes=None):
        self.policies = policies
        self.description = description
        self.notes = notes

    @property
    def exists(self):
        """Check existence of this Policy Profile.

        Returns: :py:class:`bool` signalizing the presence of the Policy Profile in database.
        """
        miq_sets = cfmedb()["miq_sets"]
        return cfmedb().session\
            .query(miq_sets.description)\
            .filter(
                miq_sets.description == self.description and miq_sets.set_type == "MiqPolicySet")\
            .count() > 0

    def create(self, cancel=False):
        """Create this Policy Profile.

        Args:
            cancel: Whether to cancel the operation.
        """
        policy_list = []
        for policy in self.policies:
            if isinstance(policy, BasePolicy):
                if not policy.exists:
                    policy.create()
                    assert policy.exists, "Unable to create a policy {}!".format(str(policy))
            policy_list.append(str(policy))
        sel.force_navigate("policy_profile_new")
        fill(
            self.form,
            dict(description=self.description, notes=self.notes, policies=policy_list),
            action=form_buttons.cancel if cancel else form_buttons.add
        )
        flash.assert_no_errors()

    def update(self, updates, cancel=False):
        """Update informations, verify presence of policies, navigate to page and update the info.

        Args:
            updates: Provided by update() context manager.
            cancel: Whether to cancel the update.
        """
        if "description" in updates:
            self.description = updates["description"]

        policy_list = None
        if "policies" in updates:
            self.policies = updates["policies"]
            policy_list = []
            for policy in self.policies:
                if isinstance(policy, BasePolicy):
                    if not policy.exists:
                        policy.create()
                        assert policy.exists, "Unable to create a policy {}!".format(str(policy))
                policy_list.append(str(policy))
        if "notes" in updates:
            self.notes = updates["notes"]
        sel.force_navigate("policy_profile_edit", context={"policy_profile_name": self.description})
        fill(
            self.form,
            dict(description=self.description, notes=self.notes, policies=policy_list)
        )
        form_buttons.cancel() if cancel else form_buttons.save()
        flash.assert_no_errors()

    def delete(self, cancel=False):
        """Delete this Policy Profile. Does not delete child policies.

        Args:
            cancel: Whether to cancel the operation.
        """
        sel.force_navigate("policy_profile", context={"policy_profile_name": self.description})
        cfg_btn("Remove this Policy Profile", invokes_alert=True)
        sel.handle_alert(cancel)
        flash.assert_no_errors()


class BaseAlertProfile(Updateable, Pretty):
    """This class represents an Alert Profile.

    Alerts can be assigned to Alert Profile and also the Alert Profile can be assigned to various
    objects.

    Example:

        >> from cfme.control.explorer import Alert, VMInstanceAlertProfile
        >> p = VMInstanceAlertProfile("aprofile",
        ..     alerts=[Alert("somealert", timeline_event=True, driving_event="Hourly Timer")])
        >> p.create()
        >> p.assign_to("The Enterprise")
        >> with update(p):
        ..     p.notes = "Notes!"
        >> p.delete()

    Args:
        description: Name of the Alert Profile.
        alerts: Iterable with alerts. Can be of :py:class:`str` but also objects of
            :py:class:`Alert` can be used, then Alert Profile checks for presence of alerts and
            if they aren't created yet, it will create them.
        notes: Notes for the Alert Profile.
    """
    PREFIX = None
    TYPE = None

    form = Form(
        fields=[
            ("description", Input("description")),
            ("notes", "textarea#notes"),
            ("alerts", MultiBoxSelect.default())
        ]
    )

    selected_form = Form(
        fields=[
            ("selections",
             CheckboxTree("//div[@id='obj_treebox']/div/table|//div[@id='obj_treebox']/ul"))]
    ),

    buttons = Region(
        locators=dict(
            add=form_buttons.add,
            cancel=form_buttons.cancel,
            save=form_buttons.save,
            reset=form_buttons.reset,
        )
    )

    assignments = Form(
        fields=[
            ("assign", {
                version.LOWEST: Select("select#chosen_assign_to"),
                "5.5": AngularSelect("chosen_assign_to")}),
        ]
    )

    sub_assignments = {
        "<Nothing>": Form(fields=[]),
        "The Enterprise": Form(fields=[]),
        "Selected Clusters": selected_form,
        "Selected Folders": selected_form,
        "Selected Hosts": selected_form,
        "Selected Infrastructure Providers": selected_form,
        "Selected Resource Pools": selected_form,
        "Selected Hosts": selected_form,
        "Tagged Clusters": selected_form,
        "Tagged Hosts": selected_form,
        "Tagged Clusters": selected_form,
        "Tagged Infrastructure Providers": selected_form,
        "Tagged Clusters": selected_form,
        "Tagged Resource Pools": selected_form,
        "Tagged VMs and Instances": selected_form
    }

    pretty_attrs = ['description', 'alerts']

    def __init__(self, description, alerts=None, notes=None):
        assert self.PREFIX, "You must use inherited class of this!"
        self.alerts = alerts
        self.description = description
        self.notes = notes

    @property
    def exists(self):
        """Check existence of this Alert Profile.

        Returns: :py:class:`bool` signalizing the presence of the Alert Profile in database.
        """
        miq_sets = cfmedb()["miq_sets"]
        return cfmedb().session\
            .query(miq_sets.description)\
            .filter(
                miq_sets.description == self.description and miq_sets.set_type == "MiqAlertSet")\
            .count() > 0

    def create(self, cancel=False):
        """Create this Alert Profile.

        Args:
            cancel: Whether to cancel the operation.
        """
        for alert in self.alerts:
            if isinstance(alert, Alert) and not alert.exists:
                alert.create()
                assert alert.exists, "Could not create an Alert!"
        sel.force_navigate("{}_alert_profile_new".format(self.PREFIX))
        fill(self.form, dict(
            description=self.description,
            notes=self.notes,
            alerts=self.alerts,
        ))
        if not cancel:
            form_buttons.add()
        else:
            form_buttons.cancel()
        flash.assert_no_errors()

    def update(self, updates, cancel=False):
        """ Update informations, verify presence of alerts, navigate to page and update the info.

        Args:
            updates: Provided by update() context manager.
            cancel: Whether to cancel the update.
        """
        if "description" in updates:
            self.description = updates["description"]

        if "alerts" in updates:
            self.alerts = updates["alerts"]
            for alert in self.alerts:
                if isinstance(alert, Alert) and not alert.exists:
                    alert.create()
                    assert alert.exists, "Could not create an Alert!"
        if "notes" in updates:
            self.notes = updates["notes"]
        sel.force_navigate("{}_alert_profile_edit".format(self.PREFIX),
                           context={"alert_profile_name": self.description})
        fill(self.form, dict(
            description=self.description,
            notes=self.notes,
            alerts=self.alerts,
        ))
        if not cancel:
            form_buttons.save()
        else:
            form_buttons.cancel()
        flash.assert_no_errors()

    def delete(self, cancel=False):
        """Delete this Alert Profile. Does not delete child Alerts.

        Args:
            cancel: Whether to cancel the operation.
        """
        sel.force_navigate("{}_alert_profile".format(self.PREFIX),
                           context={"alert_profile_name": self.description})
        cfg_btn("Delete this Alert Profile", invokes_alert=True)
        sel.handle_alert(cancel)
        flash.assert_no_errors()

    def assign_to(self, assign, selections=None, tag_category=None):
        """Assigns this Alert Profile to specified objects.

        Args:
            assign: Where to assign (The Enterprise, ...).
            selections: What items to check in the tree. N/A for The Enteprise.
            tag_category: Only for choices starting with Tagged. N/A for The Enterprise.
        """
        sel.force_navigate("{}_alert_profile_assignments".format(self.PREFIX),
                           context={"alert_profile_name": self.description})
        fill(self.assignments, dict(assign=assign))
        if selections or tag_category:
            fill(self.sub_assignments[assign], dict(category=tag_category, selections=selections))
        form_buttons.save()
        flash.assert_no_errors()


class ClusterAlertProfile(BaseAlertProfile):
    PREFIX = "cluster"
    TYPE = "Cluster / Deployment Role"


class DatastoreAlertProfile(BaseAlertProfile):
    PREFIX = "datastore"
    TYPE = "Datastore"


class HostAlertProfile(BaseAlertProfile):
    PREFIX = "host"
    TYPE = "Host / Node"


class MiddlewareServerAlertProfile(BaseAlertProfile):
    PREFIX = "middleware_server"
    TYPE = "Middleware Server"


class ProviderAlertProfile(BaseAlertProfile):
    PREFIX = "provider"
    TYPE = "Provider"


class ServerAlertProfile(BaseAlertProfile):
    PREFIX = "server"
    TYPE = "Server"


class VMInstanceAlertProfile(BaseAlertProfile):
    PREFIX = "vm_instance"
    TYPE = "VM and Instance"


def event_policies(event):
    """Return all policies, where specified event is assigned.

    Args:
        event: Event to examine.

    Returns: :py:class:`set` of the policies where this event is assigned.
    """
    sel.force_navigate("control_explorer_event", context={"event_name": event})
    try:
        return {policy[1].text.encode("utf-8").strip() for policy in events_policies_table.rows()}
    except NoSuchElementException:
        return set([])
