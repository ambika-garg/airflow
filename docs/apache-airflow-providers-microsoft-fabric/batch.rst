 .. Licensed to the Apache Software Foundation (ASF) under one
    or more contributor license agreements.  See the NOTICE file
    distributed with this work for additional information
    regarding copyright ownership.  The ASF licenses this file
    to you under the Apache License, Version 2.0 (the
    "License"); you may not use this file except in compliance
    with the License.  You may obtain a copy of the License at

 ..   http://www.apache.org/licenses/LICENSE-2.0

 .. Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, either express or implied.  See the License for the
    specific language governing permissions and limitations
    under the License.


Fabric Run Item Operator
=================================

FabricRunItemOperator
----------------------------------
Use the
:class:`~airflow.providers.microsoft.fabric.operators.fabric.FabricRunItemOperator` to trigger an item on Microsoft Fabric

Below is an example of using this operator to trigger a Microsoft Fabric notebook

.. exampleinclude:: /../../tests/system/providers/microsoft/fabric/example_fabric_item_run.py
    :language: python
    :dedent: 0
    :start-after: [START howto_operator_fabric_run_notebook_sync]
    :end-before: [END howto_operator_fabric_run_notebook_sync]


Reference
---------

For further information, look at:

* `Microsoft Fabric Documentation <https://learn.microsoft.com/en-us/fabric/>`__
