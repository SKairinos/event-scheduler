import typing as t
from unittest import TestCase

from pydantic import BaseModel, ValidationError


AnyValueError = t.TypeVar('AnyValueError', bound=ValueError)


class PyDanticTestCase(TestCase):
    """Base class to help with testing PyDantic models."""

    def assert_raises_validation_error(
        self,
        field_errors: t.List[t.Tuple[str, t.Type[AnyValueError]]],
        model_type: t.Type[BaseModel],
        **kwargs
    ):
        """Helper to assert the inner exceptions of a validation error.

        :param field_errors: The list of inner exception types raised per field.
        :param model_type: The PyDantic model to create an instance of. 
        """
        with self.assertRaises(ValidationError) as ctx:
            model_type(**kwargs)

        self.assertListEqual(field_errors, [
            (error._loc, type(error.exc))
            for error in ctx.exception.raw_errors
        ])
