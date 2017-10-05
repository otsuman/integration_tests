import pytest
import time

from cfme.base.credential import Credential
from cfme.base.ssui import SSUIBaseLoggedInPage
from cfme.base.ui import BaseLoggedInPage

from cfme.configure.access_control import User
from cfme.services.dashboard import Dashboard
from cfme.services.myservice import MyService
from cfme.services.service_catalogs.ssui import ServiceCatalogsView

from cfme.utils.appliance import get_or_create_current_appliance, ViaSSUI, ViaUI
from cfme.utils.appliance.implementations.ssui import navigate_to
from cfme.utils.log import logger
from cfme.utils.wait import wait_for


@pytest.mark.parametrize('context', [ViaSSUI])
def test_myservice_workload(context):

    appliance = get_or_create_current_appliance()
    ui_view = appliance.browser.create_view(BaseLoggedInPage)
    with appliance.context.use(context):

        starttime = time.time()
        appliance.server.login()

        logged_in_view = appliance.ssui.create_view(SSUIBaseLoggedInPage)
        wait_for(lambda: logged_in_view.is_displayed, delay=1, num_sec=300,
                 message="waiting for view to be displayed")
        login_timediff = time.time() - starttime
        logger.info('LoggedIn in {}'.format(login_timediff))
        myservice = MyService(appliance, 'AyTIsWEAHV')

        view = navigate_to(myservice, 'All')
        wait_for(lambda: view.service.list(view.service.list_name, 'obH8jgdJfZsdf').is_displayed,
                 delay=2, num_sec=300, message="waiting for view to be displayed")

        all_services_timediff = time.time() - starttime
        logger.info('All Services in {}'.format(all_services_timediff - login_timediff))
        time.sleep(5)
        view = navigate_to(myservice, 'Details')
        wait_for(lambda: view.is_displayed, delay=1, num_sec=300,
                 message="waiting for view to be displayed")
        details_services_timediff = time.time() - starttime
        logger.info('Service details in {}'.format(
            details_services_timediff - all_services_timediff - 5))
        view = navigate_to(Dashboard, 'DashboardAll')
        wait_for(lambda: view.is_displayed, delay=1, num_sec=300,
                 message="waiting for view to be displayed")
        dashboard_timediff = time.time() - starttime
        logger.info('dashboard details in {}'.format(
            dashboard_timediff - details_services_timediff))
        view.navigation.select('Service Catalog')
        view = appliance.ssui.create_view(ServiceCatalogsView)
        wait_for(lambda: view.is_displayed, delay=1, num_sec=300,
                 message="waiting for view to be displayed")
        catalogs_timediff = time.time() - starttime
        logger.info('catalogs details in {}'.format(
            catalogs_timediff - dashboard_timediff))

        with appliance.context.use(ViaUI):
            from cfme.utils.browser import ensure_browser_open
            ensure_browser_open(appliance.server.address())
            appliance.server.login()
            appliance = get_or_create_current_appliance()
            ui_view = appliance.browser.create_view(BaseLoggedInPage)
            ui_view.settings.expand()
            ui_view.settings.browser.move_to_element('//ul/li/a[normalize-space(.)="Change Group"]',
                                                          check_safe=False)
            ui_view.settings.browser.click('//ul/li/a[normalize-space(.)="testgroup2"]')
    with appliance.context.use(context):
        starttime = time.time()
        appliance.server.login()

        logged_in_view = appliance.ssui.create_view(SSUIBaseLoggedInPage)
        wait_for(lambda: logged_in_view.is_displayed, delay=1, num_sec=300,
                 message="waiting for view to be displayed")
        login_timediff = time.time() - starttime
        logger.info('Service: LoggedIn in {}'.format(login_timediff))
        myservice = MyService(appliance, 'AyTIsWEAHV')

        view = navigate_to(myservice, 'All')
        wait_for(
            lambda: view.service.list(view.service.list_name, 'obH8jgdJfZsdf').is_displayed,
            delay=2, num_sec=300, message="waiting for view to be displayed")

        all_services_timediff = time.time() - starttime
        logger.info('Service: All Services in {}'.format(all_services_timediff -
                                                         login_timediff))
        time.sleep(5)
        view = navigate_to(myservice, 'Details')
        wait_for(lambda: view.is_displayed, delay=1, num_sec=300,
                 message="waiting for view to be displayed")
        details_services_timediff = time.time() - starttime
        logger.info('Service: Service details in {}'.format(
            details_services_timediff - all_services_timediff - 5))
        view = navigate_to(Dashboard, 'DashboardAll')
        wait_for(lambda: view.is_displayed, delay=1, num_sec=300,
                 message="waiting for view to be displayed")
        dashboard_timediff = time.time() - starttime
        logger.info('Service: dashboard details in {}'.format(
            dashboard_timediff - details_services_timediff))
        view.navigation.select('Service Catalog')
        view = appliance.ssui.create_view(ServiceCatalogsView)
        wait_for(lambda: view.is_displayed, delay=1, num_sec=300,
                 message="waiting for view to be displayed")
        catalogs_timediff = time.time() - starttime
        logger.info('Service: catalogs details in {}'.format(
            catalogs_timediff - dashboard_timediff))

