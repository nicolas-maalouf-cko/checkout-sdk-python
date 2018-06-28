import unittest
import os
import tests
import json

import checkout_sdk as sdk

from checkout_sdk import HttpClient, Config, Validator
from checkout_sdk.payments import PaymentsClient
from tests.base import CheckoutSdkTestCase
from enum import Enum


class PaymentsClientTests(CheckoutSdkTestCase):
    def setUp(self):
        super().setUp()
        self.http_client = HttpClient(
            Config(api_base_url=tests.MOCK_API_BASE_URL))
        # self.http_client = HttpClient(Config())
        self.client = PaymentsClient(self.http_client)

    def tearDown(self):
        super().tearDown()
        self.http_client.close_session()

    def test_payments_client_full_card_auth_request(self):
        # TODO: put test values into CONSTANTS where appropriate
        try:
            payment = self.client.request(
                card={
                    'number': '4242424242424242',
                    'expiryMonth': 6,
                    'expiry_year': 2018,  # snake_case is automatically converted
                    'cvv': '100',
                    'name': 'Joe Smith',
                    'billingDetails': {
                        'addressLine1': '1 London Street',
                        'postcode': 'W1',
                        'country': 'GB',
                        'city': 'London',
                        'state': 'Central London',
                        'phone': {
                            'countryCode': '44',
                            'number': '203 123 1234'
                        }
                    }
                },
                value=100,  # cents
                currency=sdk.Currency.USD,  # or 'usd'
                payment_type=sdk.PaymentType.Recurring,
                track_id='ORDER-001-002',
                customer='joesmith@gmail.com',
                udf1='udf1',
                customer_ip='8.8.8.8',
                products=[{
                    "description": "Blue Medium",
                    "name": "T-Shirt",
                    "price": 2000,
                    "quantity": 1,
                    "shippingCost": 50,
                    "sku": "tee123"
                }]
            )

            self.assertEqual(payment.http_response.status, 200)

            # test payment
            self.assertTrue(Validator.is_id(payment.id, short_id=True))
            self.assertTrue(payment.approved)
            self.assertEqual(payment.value, 100)
            self.assertEqual(payment.currency, 'USD')
            self.assertEqual(payment.track_id, 'ORDER-001-002')

            # test card
            self.assertTrue(Validator.is_id(payment.card.id), 'card')
            # expiry month and year return as string (month is padded with 0)
            self.assertEqual(payment.card.expiryMonth, '06')
            self.assertEqual(payment.card.expiryYear, '2018')
            self.assertEqual(payment.card.last4, '4242')
            self.assertEqual(payment.card.name, 'Joe Smith')

            # test customer
            self.assertTrue(Validator.is_id(payment.customer.id, 'cust'))
            self.assertEqual(payment.customer.email, 'joesmith@gmail.com')

            # test other content from the http body
            body = payment.http_response.body

            self.assertEqual(body['card']['billingDetails']['city'], 'London')
            self.assertEqual(body['transactionIndicator'],
                             sdk.PaymentType.Recurring.value)  # pylint: disable = no-member
            self.assertEqual(body['udf1'], 'udf1')
            # below is also a test of snake >> camel casing.
            self.assertEqual(body['customerIp'], '8.8.8.8')
            self.assertEqual(body['products'][0]['price'], 2000)
        except sdk.errors.CheckoutSdkError as e:
            print(
                '{0.http_status} {0.error_code} {0.elapsed} {0.event_id} // {0.message}'.format(e))
