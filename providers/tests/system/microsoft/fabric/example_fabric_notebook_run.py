# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
This is an example dag for using the FabricRunItemOperator to trigger Microsoft Fabric notebook.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime

from airflow import DAG
from airflow.decorators import task
from airflow.models import Connection
from airflow.models.baseoperator import chain
from airflow.providers.microsoft.fabric.operators.fabric import FabricRunItemOperator
from airflow.settings import Session

DAG_ID = "run_fabric_notebook"
SYSTEM_TESTS_ENV_NAME = "SYSTEM_TESTS_FABRIC"
CONNECTION_ID = "fabric_conn"

# Connection Environment variables
CLIENT_ID = os.environ.get(f"{SYSTEM_TESTS_ENV_NAME}_CLIENT_ID")
REFRESH_TOKEN = os.environ.get(f"{SYSTEM_TESTS_ENV_NAME}_REFRESH_TOKEN", None)
TENANT_ID = os.environ.get(f"{SYSTEM_TESTS_ENV_NAME}_TENANT_ID", None)
CLIENT_SECRET = os.environ.get(f"{SYSTEM_TESTS_ENV_NAME}_CLIENT_SECRET", None)
SCOPES = os.environ.get(f"{SYSTEM_TESTS_ENV_NAME}_SCOPES", None)

# Operator Environment variables
WORKSPACE_ID = os.environ.get(f"{SYSTEM_TESTS_ENV_NAME}_WORKSPACE_ID", None)
NOTEBOOK_ID = os.environ.get(f"{SYSTEM_TESTS_ENV_NAME}_NOTEBOOK_ID", None)
PIPELINE_ID = os.environ.get(f"{SYSTEM_TESTS_ENV_NAME}_PIPELINE_ID", None)

log = logging.getLogger(__name__)

with DAG(
    DAG_ID,
    schedule="@once",
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["example", "fabric"],
) as dag:

    @task
    def create_connection(connection_id: str) -> None:
        connection = Connection(
            conn_id=connection_id,
            description="Example Microsoft Fabric connection",
            conn_type="fabric",
            login=CLIENT_ID,
            password=REFRESH_TOKEN,
            extra={"tenantId": TENANT_ID, "scopes": SCOPES, "clientSecret": CLIENT_SECRET},
        )

        session = Session()
        log.info("Removing connection %s if it exists", connection_id)
        query = session.query(Connection).filter(Connection.conn_id == connection_id)
        query.delete()

        session.add(connection)
        session.commit()
        log.info("Connection created: '%s'", connection_id)

    create_connection_task = create_connection(connection_id=CONNECTION_ID)

    # [START howto_operator_fabric_run_notebook_sync]
    run_notebook_task_sync = FabricRunItemOperator(
        task_id="run_notebook_sync",
        workspace_id="de1004ac-eef9-4851-adac-92c09719dd8e",
        item_id="ffdd7321-0938-4ad5-bfc0-f38a1000380f",
        fabric_conn_id="fabric_conn",
        job_type="RunNotebook",
        wait_for_termination=True,
        check_interval=10,
        deferrable=False,
    )
    # [END howto_operator_fabric_run_notebook_sync]

    # [START howto_operator_fabric_run_notebook_async]
    # run_notebook_task_async = FabricRunItemOperator(
    #     task_id="run_notebook_async",
    #     workspace_id="de1004ac-eef9-4851-adac-92c09719dd8e",
    #     item_id="ffdd7321-0938-4ad5-bfc0-f38a1000380f",
    #     fabric_conn_id=CONNECTION_ID,
    #     job_type="RunNotebook",
    #     wait_for_termination=True,
    #     deferrable=True,
    # )
    # [END howto_operator_fabric_run_notebook_async]

    @task(task_id="delete_connection")
    def delete_connection(connection_id: str) -> None:
        session = Session()
        log.info("Removing connection %s", connection_id)
        query = session.query(Connection).filter(Connection.conn_id == connection_id)
        query.delete()
        session.commit()

    delete_connection_task = delete_connection(connection_id=CONNECTION_ID)

    chain(
        # TEST SETUP
        create_connection_task,
        # TEST BODY
        run_notebook_task_sync,
        # run_notebook_task_async,
        # TEST TEARDOWN
        delete_connection_task,
    )

    from tests_common.test_utils.watcher import watcher

    # This test needs watcher in order to properly mark success/failure
    # when "tearDown" task with trigger rule is part of the DAG
    list(dag.tasks) >> watcher()

from tests_common.test_utils.system_tests import get_test_run  # noqa: E402

# Needed to run the example DAG with pytest (see: tests/system/README.md#run_via_pytest)
test_run = get_test_run(dag)
