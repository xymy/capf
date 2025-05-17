capf.drivers
============

.. currentmodule:: capf.drivers

Abstract Base Classes
---------------------

.. autoclass:: Driver
    :special-members: __call__

Data Source
-----------

.. autoclass:: SourceType

.. autoclass:: Source

Drivers for External Source
----------------------------

.. autoclass:: ValueDriver

.. autoclass:: ScalarDriver

.. autoclass:: ListDriver

Drivers for Internal Source
----------------------------

.. autoclass:: FlagDriver

.. autoclass:: OnFlagDriver

.. autoclass:: OffFlagDriver

Drivers Emitting Message
-------------------------

.. autoclass:: MessageDriver

.. autoclass:: HelpDriver

.. autoclass:: VersionDriver
