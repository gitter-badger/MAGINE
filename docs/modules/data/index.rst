Data management
---------------
Tools to process, organize, and query data.
The classes are derived from pandas.DataFrame, meaning everything you can do with pandas you can do with MAGINE.


BaseData is the core DataFrame. We provide functions that are commonly used.
This class is used by both "Sample" and "EnrichmentResult".

BaseData
--------

.. autoclass:: magine.data.base.BaseData
   :members:
   :undoc-members:
   :show-inheritance:


Species data
------------

.. autoclass:: magine.data.experimental_data.Sample
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: magine.data.experimental_data.ExperimentalData
   :members:
   :undoc-members:
   :show-inheritance:




