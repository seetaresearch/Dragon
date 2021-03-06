Workspace
=========

.. doxygenclass:: dragon::Workspace

Constructors
------------

.. doxygenfunction:: dragon::Workspace::Workspace(const string &name)

Public Functions
----------------

Clear
#####
.. doxygenfunction:: dragon::Workspace::Clear

CreateGraph
###########
.. doxygenfunction:: dragon::Workspace::CreateGraph

CreateTensor
############
.. doxygenfunction:: dragon::Workspace::CreateTensor

GetTensor
#########
.. doxygenfunction:: dragon::Workspace::GetTensor

HasTensor
#########
.. doxygenfunction:: dragon::Workspace::HasTensor

MergeFrom
#########
.. doxygenfunction:: dragon::Workspace::MergeFrom

RunGraph
########
.. doxygenfunction:: dragon::Workspace::RunGraph

RunOperator
###########
.. doxygenfunction:: dragon::Workspace::RunOperator

SetAlias
########
.. doxygenfunction:: dragon::Workspace::SetAlias

TryGetTensor
############
.. doxygenfunction:: dragon::Workspace::TryGetTensor

UniqueName
##########
.. doxygenfunction:: dragon::Workspace::UniqueName

data
####
.. doxygenfunction:: dragon::Workspace::data(const vector<size_t> &segments, const string &name = "data:0")

data
####
.. doxygenfunction:: dragon::Workspace::data(const vector<int64_t> &segments, const string &name = "data:0")

graphs
######
.. doxygenfunction:: dragon::Workspace::graphs

name
####
.. doxygenfunction:: dragon::Workspace::name

tensors
#######
.. doxygenfunction:: dragon::Workspace::tensors

.. raw:: html

  <style>
    h1:before {
      content: "dragon::";
      color: #103d3e;
    }
  </style>
