
class DependencyManager:
    def __init__(self) -> None:
        # to avoid circular dependency
        self.params: dict[str, "Param"] = {}
        self.dependencies = {}  # {source_param: [(target_param, dep_type, update_fn)]}

    def add_param(self, param):
        self.params[param.name] = param
        param.manager = self

    def add_dependency(self, source_param, target_param, update_fn):
        self.dependencies.setdefault(source_param.name, []).append(
            (target_param, update_fn)
        )

    def notify_change(self, source_param):
        for target_param, update_fn in self.dependencies.get(source_param.name, []):
            update_fn(target_param, source_param)
