capf.validators
===============

.. currentmodule:: capf.validators

Abstract Base Classes
---------------------

.. autoclass:: Validator
    :special-members: __call__

Validators for Basic Types
--------------------------

.. autoclass:: StrValidator

.. autoclass:: BoolValidator

.. autoclass:: IntValidator

.. autoclass:: FloatValidator

Validators for Choice
---------------------

.. autoclass:: ChoiceValidator

.. autoclass:: StrChoiceValidator

.. autoclass:: IntChoiceValidator

.. autoclass:: FloatChoiceValidator

Validators for Range
--------------------

.. autoclass:: RangeValidator

.. autoclass:: IntRangeValidator

.. autoclass:: FloatRangeValidator

Validators for Date and Time
----------------------------

.. autoclass:: DateTimeValidator

Validators for Filesystem Path
------------------------------

.. autoclass:: PathValidator

.. autoclass:: DirPathValidator

.. autoclass:: FilePathValidator

Functions
---------

.. autofunction:: resolve_validator
