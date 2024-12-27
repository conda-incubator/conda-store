{{/*
Expand the name of the chart.
*/}}
{{- define "condaStore.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "condaStore.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "condaStore.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "condaStore.labels" -}}
helm.sh/chart: {{ include "condaStore.chart" . }}
{{ include "condaStore.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "condaStore.selectorLabels" -}}
app.kubernetes.io/name: {{ include "condaStore.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Set's the worker resources if the user has set any.
*/}}
{{- define "worker.resources" -}}
  {{- if .Values.worker.resources -}}
          resources:
{{ toYaml .Values.worker.resources | indent 12}}
  {{ end }}
{{- end -}}

{{/*
Set's the uiServer resources if the user has set any.
*/}}
{{- define "uiServer.resources" -}}
  {{- if .Values.uiServer.resources -}}
          resources:
{{ toYaml .Values.uiServer.resources | indent 12}}
  {{ end }}
{{- end -}}

{{/*
Set's the apiServer resources if the user has set any.
*/}}
{{- define "apiServer.resources" -}}
  {{- if .Values.apiServer.resources -}}
          resources:
{{ toYaml .Values.apiServer.resources | indent 12}}
  {{ end }}
{{- end -}}
