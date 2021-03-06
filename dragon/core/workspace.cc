#include "dragon/core/workspace.h"
#include "dragon/core/graph.h"
#include "dragon/core/operator.h"

namespace dragon {

Workspace::Workspace(const string& name) : name_(name) {
  CreateTensor(""); // Empty placeholder
  CreateTensor("flagged/recomp")
      ->Reshape({})
      ->mutable_data<bool, CPUContext>()[0] = false;
}

void Workspace::MergeFrom(Workspace* other) {
  if (other != nullptr) {
    // Add the external tensors
    for (const auto& it : other->tensor_map_) {
      if (!it.first.empty() && !str::startswith(it.first, "/")) {
        external_tensor_map_[it.first] = it.second.get();
      }
    }
    // Recount the unique index to avoid duplicate names
    for (const auto& i : other->unique_index_map_) {
      auto& index_map = unique_index_map_[i.first];
      for (const auto& j : i.second) {
        index_map[j.first] = std::max(index_map[j.first], j.second);
      }
    }
  }
}

void Workspace::Clear() {
  // Following resources usually take large memory blob.
  // It's necessary to clear them manually if workspace referenced
  // by the frontend GC circularly.
  graph_map_.clear();
  operator_map_.clear();
  for (const auto& it : tensor_map_) {
    // The tensor pointer may be referenced by the frontend.
    // Reset memory only to avoid the dangling pointer.
    it.second->Reset();
  }
  // Reinitialize the tensor flags
  GetTensor("flagged/recomp")
      ->Reshape({})
      ->mutable_data<bool, CPUContext>()[0] = false;
}

Tensor* Workspace::TryGetTensor(const string& name, bool external) const {
  // Check the alias firstly
  const auto& alias_it = alias_map_.find(name);
  auto name_v2 = alias_it != alias_map_.end() ? alias_it->second : name;
  // Search this workspace
  const auto& it = tensor_map_.find(name_v2);
  if (it != tensor_map_.end()) return it->second.get();
  if (external) {
    // Search external workspaces
    const auto& it = external_tensor_map_.find(name_v2);
    if (it != external_tensor_map_.end()) return it->second;
  }
  return nullptr;
}

Tensor* Workspace::CreateTensor(const string& name) {
  auto* tensor = TryGetTensor(name);
  // Create only if name not existed
  if (tensor == nullptr) {
    tensor = new Tensor(name);
    tensor_map_[name] = unique_ptr<Tensor>(tensor);
  }
  return tensor;
}

Tensor* Workspace::GetTensor(const string& name, bool external) const {
  auto* tensor = TryGetTensor(name, external);
  CHECK(tensor) << "\nTensor(" << name << ") is not in current workspace.";
  return tensor;
}

void Workspace::RunOperator(const OperatorDef& def) {
  string cache_key;
  OperatorBase* execute_op = nullptr;
  if (!def.arg().empty()) {
    const auto& arg = *(def.arg().end() - 1);
    if (arg.name() == "cache_key") cache_key = arg.s();
  }
  if (cache_key.empty()) {
    execute_op = OperatorBase::New(def, this);
    execute_op->Run();
    delete execute_op;
  } else {
    const auto& iter = operator_map_.find(cache_key);
    if (iter == operator_map_.end()) {
      execute_op = OperatorBase::New(def, this);
      operator_map_[cache_key] = unique_ptr<OperatorBase>(execute_op);
    } else {
      execute_op = iter->second.get();
    }
    execute_op->DeriveFrom(def)->Run();
  }
}

GraphBase* Workspace::CreateGraph(const GraphDef& def) {
  CHECK(def.has_name()) << "\nExcepted non-empty graph name.";
  GraphDef def_v2(def); // Copy to set an unique name
  def_v2.set_name(UniqueName(def.name(), "", "Graph", false));
  LOG(DEBUG) << "Create: " << def_v2.name();
  auto* graph = GraphBase::New(def_v2, this);
  graph_map_[def_v2.name()] = unique_ptr<GraphBase>(graph);
  return graph;
}

void Workspace::RunGraph(
    const string& name,
    const string& include,
    const string& exclude,
    const int stream) {
  CHECK(graph_map_.count(name))
      << "\nGraph " << name << " is not in current workspace.";
  graph_map_[name]->Run(stream, include, exclude);
}

string Workspace::UniqueName(
    const string& name,
    const string& suffix,
    const string& scope,
    bool zero_based) {
  auto& index_map = unique_index_map_[scope];
  auto required_name = name + suffix;
  auto index = index_map[required_name]++;
  if (index > 0) return name + "_" + str::to(index) + suffix;
  if (zero_based) return required_name;
  return name + "_" + str::to(index_map[required_name]++) + suffix;
}

vector<string> Workspace::tensors(bool external) const {
  vector<string> names;
  for (const auto& it : tensor_map_) {
    names.emplace_back(it.first);
  }
  if (external) {
    for (const auto& it : external_tensor_map_) {
      names.emplace_back(it.first);
    }
  }
  return names;
}

vector<string> Workspace::graphs() const {
  vector<string> names;
  for (const auto& it : graph_map_) {
    names.emplace_back(it.first);
  }
  return names;
}

} // namespace dragon
