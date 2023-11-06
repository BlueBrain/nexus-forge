from time import perf_counter
from typing import TYPE_CHECKING, List, Optional, Set, Tuple, Type, Union

from rdflib import BNode, Literal, URIRef
import pyshacl
from pyshacl.consts import (
    SH_Info,
    SH_resultSeverity,
    SH_Warning,
)
from pyshacl.errors import ConstraintLoadError, ConstraintLoadWarning, ReportableRuntimeError
from pyshacl.pytypes import GraphLike

if TYPE_CHECKING:
    from pyshacl.constraints import ConstraintComponent


def shape_validate(
        self,
        target_graph: GraphLike,
        focus: Optional[
            Union[
                Tuple[Union[URIRef, BNode]],
                List[Union[URIRef, BNode]],
                Set[Union[URIRef, BNode]],
                Union[URIRef, BNode],
            ]
        ] = None,
        abort_on_first: Optional[bool] = False,
        allow_infos: Optional[bool] = False,
        allow_warnings: Optional[bool] = False,
        _evaluation_path: Optional[List] = None,
):
    if self.deactivated:
        if self.sg.debug:
            self.logger.debug(f"Skipping shape because it is deactivated: {str(self)}")
        return True, []
    if focus is not None:
        lh_shape = False
        rh_shape = True
        self.logger.debug(f"Running evaluation of Shape {str(self)}")
        if not isinstance(focus, (tuple, list, set)):
            focus = [focus]
        self.logger.debug(f"Shape was passed {len(focus)} Focus Node/s to evaluate.")
        if len(focus) < 1:
            return True, []
    else:
        lh_shape = True
        rh_shape = False
        self.logger.debug(f"Checking if Shape {str(self)} defines its own targets.")
        self.logger.debug("Identifying targets to find focus nodes.")
        focus = self.focus_nodes(target_graph)
        self.logger.debug(f"Found {len(focus)} Focus Nodes to evaluate.")
        if len(focus) < 1:
            # It's possible for shapes to have _no_ focus nodes
            # (they are called in other ways)
            if self.sg.debug:
                self.logger.debug(f"Skipping shape {str(self)} because it found no focus nodes.")
            return True, []
        else:
            self.logger.debug(f"Running evaluation of Shape {str(self)}")
    if _evaluation_path is None:
        _evaluation_path = []
    elif len(_evaluation_path) >= 40:
        # 27 is the depth required to successfully do the meta-shacl test on shacl.ttl
        path_str = " -> ".join((str(e) for e in _evaluation_path))
        raise ReportableRuntimeError("Evaluation path too deep!\n{}".format(path_str))

    t1 = perf_counter()
    # Lazy import here to avoid an import loop
    CONSTRAINT_PARAMETERS, PARAMETER_MAP = getattr(pyshacl, 'CONSTRAINT_PARAMS', (None, None))
    if not CONSTRAINT_PARAMETERS or not PARAMETER_MAP:
        from pyshacl.constraints import ALL_CONSTRAINT_PARAMETERS, CONSTRAINT_PARAMETERS_MAP
        setattr(pyshacl, 'CONSTRAINT_PARAMS', (ALL_CONSTRAINT_PARAMETERS, CONSTRAINT_PARAMETERS_MAP))
        CONSTRAINT_PARAMETERS = ALL_CONSTRAINT_PARAMETERS
        PARAMETER_MAP = CONSTRAINT_PARAMETERS_MAP
    if self.sg.js_enabled or self._advanced:
        search_parameters = CONSTRAINT_PARAMETERS.copy()
        constraint_map = PARAMETER_MAP.copy()
        if self._advanced:
            from pyshacl.constraints.advanced import ExpressionConstraint, SH_expression

            search_parameters.append(SH_expression)
            constraint_map[SH_expression] = ExpressionConstraint
        if self.sg.js_enabled:
            from pyshacl.extras.js.constraint import JSConstraint, SH_js

            search_parameters.append(SH_js)
            constraint_map[SH_js] = JSConstraint
    else:
        search_parameters = CONSTRAINT_PARAMETERS
        constraint_map = PARAMETER_MAP
    parameters = (p for p, v in self.sg.predicate_objects(self.node) if p in search_parameters)
    reports = []
    focus_value_nodes = self.value_nodes(target_graph, focus)
    filter_reports: bool = False
    allow_conform: bool = False
    allowed_severities: Set[URIRef] = set()
    if allow_infos:
        allowed_severities.add(SH_Info)
    if allow_warnings:
        allowed_severities.add(SH_Info)
        allowed_severities.add(SH_Warning)
    if allow_infos or allow_warnings:
        if self.severity in allowed_severities:
            allow_conform = True
        else:
            filter_reports = True

    non_conformant = False
    done_constraints = set()
    run_count = 0
    _evaluation_path.append(self)
    if self.sg.debug:
        path_str = " -> ".join((str(e) for e in _evaluation_path))
        self.logger.debug(f"Current shape evaluation path: {path_str}")
    constraint_components = [constraint_map[p] for p in iter(parameters)]
    constraint_component: Type['ConstraintComponent']
    for constraint_component in constraint_components:
        if constraint_component in done_constraints:
            continue
        try:
            # if self.sg.debug:
            #     self.logger.debug(f"Constructing Constraint Component: {repr(constraint_component)}")
            c = constraint_component(self)
        except ConstraintLoadWarning as w:
            self.logger.warning(repr(w))
            continue
        except ConstraintLoadError as e:
            self.logger.error(repr(e))
            raise e
        _e_p_copy = _evaluation_path[:]
        _e_p_copy.append(c)
        if self.sg.debug:
            self.logger.debug(f"Checking conformance for constraint: {str(c)}")
        ct1 = perf_counter()
        if self.sg.debug:
            path_str = " -> ".join((str(e) for e in _e_p_copy))
            self.logger.debug(f"Current constraint evaluation path: {path_str}")
        _is_conform, _reports = c.evaluate(target_graph, focus_value_nodes, _e_p_copy)
        ct2 = perf_counter()
        if self.sg.debug:
            elapsed = ct2 - ct1
            self.logger.debug(
                f"Milliseconds to check constraint {str(c)}: {elapsed * 1000.0:.3f}ms")
            if _is_conform:
                self.logger.debug(f"DataGraph conforms to constraint {c}.")
            elif allow_conform:
                self.logger.debug(
                    f"Focus nodes do _not_ conform to constraint {c} but given severity is allowed.")
            else:
                self.logger.debug(f"Focus nodes do _not_ conform to constraint {c}.")
                if lh_shape or (not rh_shape):
                    for v_str, v_node, v_parts in _reports:
                        self.logger.debug(v_str)

        if _is_conform or allow_conform:
            ...
        elif filter_reports:
            all_allow = True
            for v_str, v_node, v_parts in _reports:
                severity_bits = list(
                    filter(lambda p: p[0] == v_node and p[1] == SH_resultSeverity, v_parts))
                if severity_bits:
                    all_allow = all_allow and (severity_bits[0][2] in allowed_severities)
            non_conformant = non_conformant or (not all_allow)
        else:
            non_conformant = non_conformant or (not _is_conform)
        reports.extend(_reports)
        run_count += 1
        done_constraints.add(constraint_component)
        if non_conformant and abort_on_first:
            break
    applicable_custom_constraints = self.find_custom_constraints()
    for a in applicable_custom_constraints:
        if non_conformant and abort_on_first:
            break
        _e_p_copy2 = _evaluation_path[:]
        validator = a.make_validator_for_shape(self)
        _e_p_copy2.append(validator)
        _is_conform, _r = validator.evaluate(target_graph, focus_value_nodes, _e_p_copy2)
        non_conformant = non_conformant or (not _is_conform)
        reports.extend(_r)
        run_count += 1
    t2 = perf_counter()
    if self.sg.debug:
        elapsed = t2 - t1
        self.logger.debug(f"Milliseconds to evaluate shape {str(self)}: {elapsed * 1000.0:.3f}ms")
    # print(_evaluation_path, "Passes" if not non_conformant else "Fails")
    return (not non_conformant), reports
