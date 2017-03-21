"""
Mixins for the EnterpriseApiClient.
"""
import json
import mock

import httpretty
from django.conf import settings
from django.core.cache import cache


class EnterpriseServiceMockMixin(object):
    """
    Mocks for the Enterprise service responses.
    """

    def setUp(self):
        super(EnterpriseServiceMockMixin, self).setUp()
        cache.clear()

    @staticmethod
    def get_enterprise_url(path):
        """Return a URL to the configured Enterprise API. """
        return '{}{}/'.format(settings.ENTERPRISE_API_URL, path)

    def mock_enterprise_course_enrollment_post_api(  # pylint: disable=invalid-name
            self,
            username='test_user',
            course_id='course-v1:edX+DemoX+Demo_Course',
            consent_granted=True
    ):
        """
        Helper method to register the enterprise course enrollment API POST endpoint.
        """
        api_response = {
            username: username,
            course_id: course_id,
            consent_granted: consent_granted,
        }
        api_response_json = json.dumps(api_response)
        httpretty.register_uri(
            method=httpretty.POST,
            uri=self.get_enterprise_url('enterprise-course-enrollment'),
            body=api_response_json,
            content_type='application/json'
        )

    def mock_enterprise_course_enrollment_post_api_failure(self):  # pylint: disable=invalid-name
        """
        Helper method to register the enterprise course enrollment API endpoint for a failure.
        """
        httpretty.register_uri(
            method=httpretty.POST,
            uri=self.get_enterprise_url('enterprise-course-enrollment'),
            body='{}',
            content_type='application/json',
            status=500
        )


class EnterpriseTestConsentRequired(object):
    """
    Mixin to help test the data_sharing_consent_required decorator.
    """
    def verify_consent_required(self, client, url, status_code=200):
        """
        Verify that the given URL redirects to the consent page when consent is required,
        and doesn't redirect to the consent page when consent is not required.

        Arguments:
        * self: ignored
        * client: the TestClient instance to be used
        * url: URL to test
        * status_code: expected status code of URL when no data sharing consent is required.
        """
        with mock.patch('util.enterprise_helpers.enterprise_enabled', return_value=True):
            with mock.patch('util.enterprise_helpers.consent_necessary_for_course') as mock_consent_necessary:
                # Ensure that when consent is necessary, the user is redirected to the consent page.
                mock_consent_necessary.return_value = True
                response = client.get(url)
                assert response.status_code == 302
                assert 'grant_data_sharing_permissions' in response.url  # pylint: disable=no-member

                # Ensure that when consent is not necessary, the user continues through to the requested page.
                mock_consent_necessary.return_value = False
                response = client.get(url)
                assert response.status_code == status_code

                # If we were expecting a redirect, ensure it's not to the data sharing permission page
                if status_code == 302:
                    assert 'grant_data_sharing_permissions' not in response.url  # pylint: disable=no-member
                return response