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
from __future__ import annotations

import asyncio
import logging
import time
from typing import AsyncIterator

from airflow.providers.microsoft.powerbi.hooks.fabric import FabricAsyncHook, FabricRunItemStatus
from airflow.triggers.base import BaseTrigger, TriggerEvent

logger = logging.getLogger(__name__)


class FabricTrigger(BaseTrigger):
    """Trigger when a Fabric item run finishes."""

    def __init__(
        self,
        fabric_conn_id: str,
        item_run_id: str,
        workspace_id: str,
        item_id: str,
        job_type: str,
        end_time: float,
        check_interval: int = 60,
        wait_for_termination: bool = True,
    ):
        super().__init__()
        self.fabric_conn_id = fabric_conn_id
        self.item_run_id = item_run_id
        self.workspace_id = workspace_id
        self.item_id = item_id
        self.job_type = job_type
        self.end_time = end_time
        self.check_interval = check_interval
        self.wait_for_termination = wait_for_termination

    def serialize(self):
        """Serialize the FabricTrigger instance."""
        return (
            "airflow.providers.microsoft.powerbi.triggers.fabric.FabricTrigger",
            {
                "fabric_conn_id": self.fabric_conn_id,
                "item_run_id": self.item_run_id,
                "workspace_id": self.workspace_id,
                "item_id": self.item_id,
                "job_type": self.job_type,
                "end_time": self.end_time,
                "check_interval": self.check_interval,
                "wait_for_termination": self.wait_for_termination,
            },
        )

    async def run(self) -> AsyncIterator[TriggerEvent]:
        """Make async connection to the fabric and polls for the item run status."""
        hook = FabricAsyncHook(fabric_conn_id=self.fabric_conn_id)
        try:
            while self.end_time > time.monotonic():
                try:
                    item_run_details = await hook.get_item_run_details(
                        item_run_id=self.item_run_id,
                        workspace_id=self.workspace_id,
                        item_id=self.item_id,
                    )
                    item_run_staus = item_run_details["status"]

                    if item_run_staus == FabricRunItemStatus.COMPLETED:
                        yield TriggerEvent(
                            {
                                "status": "success",
                                "message": f"The item run {self.item_run_id} has status {item_run_staus}.",
                                "run_id": self.item_run_id,
                            }
                        )
                        return
                    elif item_run_staus in FabricRunItemStatus.FAILURE_STATES:
                        yield TriggerEvent(
                            {
                                "status": "error",
                                "message": f"The item run {self.item_run_id} has status {item_run_staus}.",
                                "run_id": self.item_run_id,
                            }
                        )
                        return

                    self.log.info(
                        "Sleeping for %s. The pipeline state is %s.",
                        self.check_interval,
                        item_run_staus,
                    )
                    await asyncio.sleep(self.check_interval)
                except Exception as error:
                    yield TriggerEvent(
                        {
                            "status": "error",
                            "message": str(error),
                            "run_id": self.item_run_id,
                        }
                    )
            yield TriggerEvent(
                {
                    "status": "error",
                    "message": f"The item run {self.item_run_id} has {item_run_staus}.",
                    "run_id": self.item_run_id,
                }
            )
        except Exception as error:
            try:
                await hook.cancel_item_run(
                    run_id=self.item_run_id,
                    workspace_id=self.workspace_id,
                    item_id=self.item_id,
                )
                self.log.info(
                    "Unexpected error %s caught. Cancel pipeline run %s",
                    error,
                    self.item_run_id,
                )
                yield TriggerEvent(
                    {
                        "status": "error",
                        "message": str(error),
                        "run_id": self.item_run_id,
                    }
                )
                return
            except Exception as error:
                yield TriggerEvent(
                    {
                        "status": "error",
                        "message": str(error),
                        "run_id": self.item_run_id,
                    }
                )
