# Copyright 2026 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from flask import Flask
from prometheus_flask_exporter import RESTfulPrometheusMetrics

if TYPE_CHECKING:
    from flask_restful import Api
    from prometheus_client import CollectorRegistry


def init_flask_metrics(
    app: Flask,
    api: Api,
    metrics_decorator: Callable[[Callable[..., Any]], Callable[..., Any]] | None = None,
    registry: CollectorRegistry | None = None,
) -> RESTfulPrometheusMetrics:
    """Instrument a Flask-RESTful app and serve its metrics at <api prefix>/metrics.

    The route has no authentication, like the wazo-prometheus-exporter plugin it
    replaces: services must deny it in their nginx location file, or restrict it
    with `metrics_decorator` when they listen on a public interface.

    `app` is passed explicitly because `api.app` is None when the Api is
    attached to the app later with `api.init_app(app)`.
    """
    return RESTfulPrometheusMetrics(
        app,
        api,
        path=f'{api.prefix}/metrics',
        group_by='endpoint',
        metrics_decorator=metrics_decorator,
        registry=registry,
    )
