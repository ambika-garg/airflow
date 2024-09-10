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
import time
from typing import AsyncIterator

from airflow.providers.microsoft.fabric.hooks.fabric import FabricAsyncHook, FabricRunItemStatus
from airflow.triggers.base import BaseTrigger, TriggerEvent


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
            "airflow.providers.microsoft.fabric.triggers.fabric.FabricTrigger",
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
                item_run_details = await hook.async_get_item_run_details(
                    item_run_id=self.item_run_id,
                    workspace_id=self.workspace_id,
                    item_id=self.item_id,
                )
                item_run_status = item_run_details["status"]
                if item_run_status == FabricRunItemStatus.COMPLETED:
                    yield TriggerEvent(
                        {
                            "status": "success",
                            "message": f"The item run {self.item_run_id} has status {item_run_status}.",
                            "run_id": self.item_run_id,
                            "item_run_status": item_run_status,
                        }
                    )
                    return
                elif item_run_status in FabricRunItemStatus.FAILURE_STATES:
                    yield TriggerEvent(
                        {
                            "status": "error",
                            "message": f"The item run {self.item_run_id} has status {item_run_status}.",
                            "run_id": self.item_run_id,
                            "item_run_status": item_run_status,
                        }
                    )
                    return

                self.log.info(
                    "Sleeping for %s. The item state is %s.",
                    self.check_interval,
                    item_run_status,
                )
                await asyncio.sleep(self.check_interval)
            # Timeout reached
            yield TriggerEvent(
                {
                    "status": "error",
                    "message": f"Timeout reached: The item run {self.item_run_id} has {item_run_status}.",
                    "run_id": self.item_run_id,
                }
            )
        except Exception as error:
            try:
                self.log.info(
                    "Unexpected error %s caught. Cancel pipeline run %s",
                    error,
                    self.item_run_id,
                )
                await hook.cancel_item_run(
                    item_run_id=self.item_run_id,
                    workspace_id=self.workspace_id,
                    item_id=self.item_id,
                )
                yield TriggerEvent(
                    {
                        "status": "error",
                        "message": str(error),
                        "run_id": self.item_run_id,
                        "item_run_status": FabricRunItemStatus.CANCELLED,
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
                return