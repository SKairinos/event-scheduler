import typing as t
from unittest import TestCase

from pydantic import BaseModel, ValidationError


AnyValueError = t.TypeVar('AnyValueError', bound=ValueError)


class PyDanticTestCase(TestCase):
    def assert_raises_validation_error(
        self,
        field_errors: t.List[t.Tuple[str, t.Type[AnyValueError]]],
        model_type: t.Type[BaseModel],
        **kwargs
    ):
        with self.assertRaises(ValidationError) as ctx:
            model_type(**kwargs)

        self.assertListEqual(field_errors, [
            (error._loc, type(error.exc))
            for error in ctx.exception.raw_errors
        ])
