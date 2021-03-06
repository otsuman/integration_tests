"""``setup_provider`` fixture

In test modules paramatrized with :py:func:`utils.testgen.providers_by_class` (should be
just about any module that needs a provider to run its tests), this fixture will set up
the single provider needed to run that test.

If the provider setup fails, this fixture will record that failure and skip future tests
using the provider.

"""
import pytest
import six

from cfme.common.provider import BaseProvider
from cfme.cloud.provider import CloudProvider
from cfme.infrastructure.provider import InfraProvider
from cfme.containers.provider import ContainersProvider
from cfme.middleware.provider import MiddlewareProvider
from fixtures.artifactor_plugin import art_client, get_test_idents
from fixtures.templateloader import TEMPLATES
from utils import providers
from utils.log import logger

# failed provider tracking for _setup_provider_fixture
_failed_providers = set()


def _setup_provider(provider_key, request=None):
    def skip(provider_key, previous_fail=False):
        if request:
            node = request.node
            name, location = get_test_idents(node)
            skip_data = {'type': 'provider', 'reason': provider_key}
            art_client.fire_hook('skip_test', test_location=location, test_name=name,
                skip_data=skip_data)
        if previous_fail:
            raise pytest.skip('Provider {} failed to set up previously in another test, '
                              'skipping test'.format(provider_key))
        else:
            raise pytest.skip('Provider {} failed to set up this time, '
                              'skipping test'.format(provider_key))
    # This function is dynamically "fixturized" to setup up a specific provider,
    # optionally skipping the provider setup if that provider has previously failed.
    if provider_key in _failed_providers:
        skip(provider_key, previous_fail=True)

    try:
        providers.setup_provider(provider_key)
    except Exception as ex:
        logger.error('Error setting up provider %s', provider_key)
        logger.exception(ex)
        _failed_providers.add(provider_key)
        skip(provider_key)


@pytest.fixture(scope='function')
def setup_provider(request, provider):
    """Function-scoped fixture to set up a provider"""
    _setup_provider(provider.key, request)


@pytest.fixture(scope='module')
def setup_provider_modscope(request, provider):
    """Function-scoped fixture to set up a provider"""
    _setup_provider(provider.key, request)


@pytest.fixture(scope='class')
def setup_provider_clsscope(request, provider):
    """Module-scoped fixture to set up a provider"""
    _setup_provider(provider.key, request)


@pytest.fixture
def setup_provider_funcscope(request, provider):
    """Function-scoped fixture to set up a provider

    Note:

        While there are cases where this is useful, provider fixtures should
        be module-scoped the majority of the time.

    """
    _setup_provider(provider.key, request)


@pytest.fixture(scope="session")
def any_provider_session():
    BaseProvider.clear_providers()  # To make it clean
    providers.setup_a_provider(validate=True, check_existing=True)


@pytest.fixture(scope="function")
def template(template_location, provider):
    if template_location is not None:
        o = provider.data
        try:
            for field in template_location:
                o = o[field]
        except (IndexError, KeyError):
            logger.info("Cannot apply %r to %r in the template specification, ignoring.", field, o)
        else:
            if not isinstance(o, six.string_types):
                raise ValueError("{!r} is not a string! (for template)".format(o))
            if not TEMPLATES:
                # There is nothing in TEMPLATES, that means no trackerbot URL and no data pulled.
                # This should normally not constitute an issue so continue.
                return o
            templates = TEMPLATES.get(provider.key, None)
            if templates is not None:
                if o in templates:
                    return o
    logger.info("Wanted template %s on %s but it is not there!", o, provider.key)
    pytest.skip('Template not available')


def _get_template(provider, template_type_name):
    template = provider.data.get(template_type_name, None)
    if template:
        if not TEMPLATES:
            # Same as couple of lines above
            return template
        templates = TEMPLATES.get(provider.key, None)
        if templates is not None:
            if template in templates:
                return template
    else:
        pytest.skip('No {} for provider {}'.format(template_type_name, provider.key))
    logger.info("Wanted template %s on %s but it is not there!", template, provider.key)
    pytest.skip('Template not available')


@pytest.fixture(scope="function")
def small_template(provider):
    return _get_template(provider, 'small_template')


@pytest.fixture(scope="module")
def small_template_modscope(provider):
    return _get_template(provider, 'small_template')


@pytest.fixture(scope="function")
def full_template(provider):
    return _get_template(provider, 'full_template')


@pytest.fixture(scope="module")
def full_template_modscope(provider):
    return _get_template(provider, 'full_template')


@pytest.fixture(scope="function")
def big_template(provider):
    return _get_template(provider, 'big_template')


@pytest.fixture(scope="module")
def big_template_modscope(provider):
    return _get_template(provider, 'big_template')


@pytest.fixture(scope="function")
def provisioning(provider):
    return provider.data['provisioning']


@pytest.fixture
def has_no_providers():
    """ Clears all management systems from an applicance

    This is a destructive fixture. It will clear all managements systems from
    the current appliance.
    """
    BaseProvider.clear_providers()


@pytest.fixture
def has_no_cloud_providers():
    """ Clears all cloud providers from an appliance

    This is a destructive fixture. It will clear all cloud managements systems from
    the current appliance.
    """
    BaseProvider.clear_providers_by_class(CloudProvider, validate=True)


@pytest.fixture
def has_no_infra_providers():
    """ Clears all infrastructure providers from an appliance

    This is a destructive fixture. It will clear all infrastructure managements systems from
    the current appliance.
    """
    BaseProvider.clear_providers_by_class(InfraProvider, validate=True)


@pytest.fixture
def has_no_containers_providers():
    """ Clears all containers providers from an appliance

    This is a destructive fixture. It will clear all container managements systems from
    the current appliance.
    """
    BaseProvider.clear_providers_by_class(ContainersProvider, validate=True)


@pytest.fixture
def has_no_middleware_providers():
    """Clear all middleware providers."""
    BaseProvider.clear_providers_by_class(MiddlewareProvider, validate=True)
