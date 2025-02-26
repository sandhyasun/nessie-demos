#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Dremio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Tests the Nessie + Iceberg + Hive Jupyter Notebook with the NBA dataset."""
import time
from typing import Any
from typing import Generator

import pytest
from _pytest.tmpdir import TempPathFactory
from assertpy import assert_that
from testbook import testbook
from testbook.client import TestbookNotebookClient

from . import _find_notebook
from . import start_nessie

num_salaries_on_experiment = "59"
num_salaries_on_main = "55"


@pytest.fixture(scope="module")
def notebook(tmpdir_factory: TempPathFactory) -> Generator:
    """Pytest fixture to run a notebook."""
    path_to_notebook = _find_notebook("nessie-iceberg-hive-demo-nba.ipynb")

    with start_nessie() as _:
        # We give sometime for Hive to start
        time.sleep(20)
        with testbook(path_to_notebook, timeout=360) as tb:
            tb.execute()
            yield tb


def _assert_that_notebook(
    text: str, notebook: TestbookNotebookClient, count: int = 0
) -> Any:
    for seen, value in enumerate(
        n for n, i in enumerate(notebook.cells) if text in i["source"]
    ):
        if seen == count:
            return assert_that(notebook.cell_output_text(value))


def test_notebook_output(notebook: TestbookNotebookClient) -> None:
    """Runs through the entire notebook and checks the output.

    :param notebook: The notebook to test
    :return:
    """
    assertion = lambda x: _assert_that_notebook(x, notebook)  # NOQA
    assertion_counted = lambda x, y: _assert_that_notebook(x, notebook, y)  # NOQA

    assertion("nessie_client = init()").contains("Hive running")

    assertion("!nessie --verbose branch").contains("main").contains("dev")

    assertion_counted(
        "current_ref.execute('SELECT COUNT(*) FROM nba.salaries')", 2
    ).contains(num_salaries_on_experiment)

    assertion_counted(
        "current_ref.execute('SELECT COUNT(*) FROM nba.salaries')", 3
    ).contains(num_salaries_on_main)


def test_dependency_setup(notebook: TestbookNotebookClient) -> None:
    """Verifies that dependencies were correctly set up.

    :param notebook: The notebook to test
    :return:
    """
    current_ref = notebook.ref("current_ref")
    assert_that(current_ref).is_not_none()
