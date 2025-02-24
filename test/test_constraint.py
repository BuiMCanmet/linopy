#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  2 22:38:48 2021.

@author: fabian
"""

import numpy as np
import pandas as pd
import pytest
from xarray.testing import assert_equal

import linopy
from linopy import EQUAL, GREATER_EQUAL, LESS_EQUAL, LinearExpression, Model
from linopy.constants import (
    long_EQUAL,
    short_GREATER_EQUAL,
    short_LESS_EQUAL,
    sign_replace_dict,
)
from linopy.constraints import Constraint


@pytest.fixture
def m():
    m = Model()
    x = m.add_variables(coords=[pd.RangeIndex(10, name="first")], name="x")
    m.add_variables(coords=[pd.Index([1, 2, 3], name="second")], name="y")
    m.add_variables(0, 10, name="z")
    m.add_constraints(x >= 0, name="c")
    return m


@pytest.fixture
def x(m):
    return m.variables["x"]


@pytest.fixture
def y(m):
    return m.variables["y"]


@pytest.fixture
def c(m):
    return m.constraints["c"]


def test_constraint_repr(c):
    c.__repr__()


def test_constraints_repr(m):
    m.constraints.__repr__()


def test_constraint_name(c):
    assert c.name == "c"


def test_empty_constraints_repr():
    # test empty contraints
    Model().constraints.__repr__()


def test_constraints_getter(m, c):
    assert c.shape == (10,)
    assert isinstance(m.constraints[["c"]], linopy.constraints.Constraints)


def test_anonymous_constraint_from_linear_expression_le(x, y):
    expr = 10 * x + y
    con = expr <= 10
    assert isinstance(con.lhs, LinearExpression)
    assert (con.sign == LESS_EQUAL).all()
    assert (con.rhs == 10).all()


def test_anonymous_constraint_from_linear_expression_ge(x, y):
    expr = 10 * x + y
    con = expr >= 10
    assert isinstance(con.lhs, LinearExpression)
    assert (con.sign == GREATER_EQUAL).all()
    assert (con.rhs == 10).all()


def test_anonymous_constraint_from_linear_expression_eq(x, y):
    expr = 10 * x + y
    con = expr == 10
    assert isinstance(con.lhs, LinearExpression)
    assert (con.sign == EQUAL).all()
    assert (con.rhs == 10).all()


def test_anonymous_constraint_from_variable_le(x):
    con = x <= 10
    assert isinstance(con.lhs, LinearExpression)
    assert (con.sign == LESS_EQUAL).all()
    assert (con.rhs == 10).all()


def test_anonymous_constraint_from_variable_ge(x):
    con = x >= 10
    assert isinstance(con.lhs, LinearExpression)
    assert (con.sign == GREATER_EQUAL).all()
    assert (con.rhs == 10).all()


def test_anonymous_constraint_from_variable_eq(x):
    con = x == 10
    assert isinstance(con.lhs, LinearExpression)
    assert (con.sign == EQUAL).all()
    assert (con.rhs == 10).all()


def test_anonymous_constraint_with_variable_on_rhs(x, y):
    expr = 10 * x + y
    con = expr == x
    assert isinstance(con.lhs, LinearExpression)
    assert (con.sign == EQUAL).all()
    assert (con.rhs == 0).all()


def test_anonymous_constraint_with_constant_on_lhs(x, y):
    expr = 10 * x + y + 10
    con = expr == 0
    assert isinstance(con.lhs, LinearExpression)
    assert (con.lhs.const == 0).all()
    assert (con.sign == EQUAL).all()
    assert (con.rhs == -10).all()


def test_anonymous_constraint_with_constant_on_rhs(x, y):
    expr = 10 * x + y
    con = expr == 10
    assert isinstance(con.lhs, LinearExpression)
    assert (con.sign == EQUAL).all()
    assert (con.rhs == 10).all()


def test_anonymous_constraint_with_expression_on_both_sides(x, y):
    expr = 10 * x + y + 10
    con = expr == expr
    assert isinstance(con.lhs, LinearExpression)
    assert con.lhs.nterm == 4  # are stacked on top of each other
    assert (con.coeffs.sum(con.term_dim) == 0).all()
    assert (con.sign == EQUAL).all()
    assert (con.rhs == 0).all()


def test_anonymous_scalar_constraint_with_scalar_variable_on_rhs(x, y):
    expr = 10 * x[0] + y[1]
    with pytest.raises(TypeError):
        con = expr == x[0]
        # assert isinstance(con.lhs, LinearExpression)
        # assert (con.sign == EQUAL).all()
        # assert (con.rhs == 0).all()


def test_anonymous_constraint_sel(x, y):
    expr = 10 * x + y
    con = expr <= 10
    assert isinstance(con.sel(first=[1, 2]), Constraint)


def test_constraint_from_rule(m, x, y):
    def bound(m, i, j):
        return (i - 1) * x[i - 1] + y[j] >= 0 if i % 2 else i * x[i] >= 0

    coords = [x.coords["first"], y.coords["second"]]
    con = Constraint.from_rule(m, bound, coords)
    assert isinstance(con, Constraint)
    assert con.lhs.nterm == 2
    repr(con)  # test repr


def test_constraint_from_rule_with_none_return(m, x, y):
    def bound(m, i, j):
        if i % 2:
            return i * x[i] + y[j] >= 0

    coords = [x.coords["first"], y.coords["second"]]
    con = Constraint.from_rule(m, bound, coords)
    assert isinstance(con, Constraint)
    assert con.lhs.nterm == 2
    assert (con.lhs.vars.loc[0, :] == -1).all()
    assert (con.lhs.vars.loc[1, :] != -1).all()
    repr(con)  # test repr


def test_constraint_vars_getter(c, x):
    assert_equal(c.vars.squeeze(), x.labels)


def test_constraint_coeffs_getter(c):
    assert (c.coeffs == 1).all()


def test_constraint_sign_getter(c):
    assert (c.sign == GREATER_EQUAL).all()


def test_constraint_rhs_getter(c):
    assert (c.rhs == 0).all()


def test_constraint_vars_setter(c, x):
    c.vars = x
    assert_equal(c.vars, x.labels)


def test_constraint_vars_setter_with_array(c, x):
    c.vars = x.labels
    assert_equal(c.vars, x.labels)


def test_constraint_vars_setter_invalid(c, x):
    with pytest.raises(TypeError):
        c.vars = pd.DataFrame(x.labels)


def test_constraint_coeffs_setter(c):
    c.coeffs = 3
    assert (c.coeffs == 3).all()


def test_constraint_lhs_setter(c, x, y):
    c.lhs = x + y
    assert c.lhs.nterm == 2
    assert c.vars.notnull().all().item()
    assert c.coeffs.notnull().all().item()


def test_constraint_lhs_setter_with_variable(c, x):
    c.lhs = x
    assert c.lhs.nterm == 1


def test_constraint_lhs_setter_with_constant(c):
    c.lhs = 10
    assert (c.rhs == -10).all()
    assert c.lhs.nterm == 0


def test_constraint_sign_setter(c):
    c.sign = EQUAL
    assert (c.sign == EQUAL).all()


def test_constraint_sign_setter_alternative(c):
    c.sign = long_EQUAL
    assert (c.sign == EQUAL).all()


def test_constraint_sign_setter_invalid(c):
    # Test that assigning lhs with other type that LinearExpression raises TypeError
    with pytest.raises(ValueError):
        c.sign = "asd"


def test_constraint_rhs_setter(c):
    c.rhs = 2
    assert (c.rhs == 2).all()


def test_constraint_rhs_setter_with_variable(c, x):
    c.rhs = x
    assert (c.rhs == 0).all()
    assert (c.coeffs.isel({c.term_dim: -1}) == -1).all()
    assert c.lhs.nterm == 2


def test_constraint_rhs_setter_with_expression(c, x, y):
    c.rhs = x + y
    assert (c.rhs == 0).all()
    assert (c.coeffs.isel({c.term_dim: -1}) == -1).all()
    assert c.lhs.nterm == 3


def test_constraint_rhs_setter_with_expression_and_constant(c, x):
    c.rhs = x + 1
    assert (c.rhs == 1).all()
    assert (c.coeffs.sum(c.term_dim) == 0).all()
    assert c.lhs.nterm == 2


def test_constraint_labels_setter_invalid(c):
    # Test that assigning labels raises FrozenInstanceError
    with pytest.raises(AttributeError):
        c.labels = c.labels


def test_constraint_sel(c):
    assert isinstance(c.sel(first=[1, 2]), linopy.constraints.Constraint)
    assert isinstance(c.isel(first=[1, 2]), linopy.constraints.Constraint)


def test_constraint_flat(c):
    assert isinstance(c.flat, pd.DataFrame)


def test_constraint_assignment_with_anonymous_constraints(m, x, y):
    m.add_constraints(x + y == 0, name="c2")
    assert m.constraints["c2"].vars.notnull().all()
    assert m.constraints["c2"].coeffs.notnull().all()


def test_constraint_assignment_sanitize_zeros(m, x, y):
    m.add_constraints(0 * x + y == 0, name="c2")
    m.constraints.sanitize_zeros()
    assert m.constraints["c2"].vars[0, 0, 0].item() == -1
    assert np.isnan(m.constraints["c2"].coeffs[0, 0, 0].item())


def test_constraint_assignment_with_args(m, x, y):
    lhs = x + y
    m.add_constraints(lhs, EQUAL, 0, name="c2")
    assert m.constraints["c2"].vars.notnull().all()
    assert m.constraints["c2"].coeffs.notnull().all()
    assert (m.constraints["c2"].sign == EQUAL).all()
    assert (m.constraints["c2"].rhs == 0).all()


def test_constraint_assignment_with_args_valid_sign(m, x, y):
    lhs = x + y
    for i, sign in enumerate([EQUAL, GREATER_EQUAL, LESS_EQUAL]):
        m.add_constraints(lhs, sign, 0, name=f"c{i}")
        assert m.constraints[f"c{i}"].vars.notnull().all()
        assert m.constraints[f"c{i}"].coeffs.notnull().all()
        assert (m.constraints[f"c{i}"].sign == sign).all()
        assert (m.constraints[f"c{i}"].rhs == 0).all()


def test_constraint_assignment_with_args_alternative_sign(m, x, y):
    lhs = x + y

    for i, sign in enumerate([long_EQUAL, short_GREATER_EQUAL, short_LESS_EQUAL]):
        m.add_constraints(lhs, sign, 0, name=f"c{i}")
        assert m.constraints[f"c{i}"].vars.notnull().all()
        assert m.constraints[f"c{i}"].coeffs.notnull().all()
        assert (m.constraints[f"c{i}"].sign == sign_replace_dict[sign]).all()
        assert (m.constraints[f"c{i}"].rhs == 0).all()


def test_constraint_assignment_with_args_invalid_sign(m, x, y):
    lhs = x + y
    with pytest.raises(ValueError):
        m.add_constraints(lhs, ",", 0)


def test_constraint_matrix(m):
    A = m.constraints.to_matrix()
    assert A.shape == (10, 14)


def test_constraint_matrix_masked_variables():
    """
    Test constraint matrix with missing variables.

    In this case the variables that are used in the constraints are
    missing. The matrix shoud not be built for constraints which have
    variables which are missing.
    """
    # now with missing variables
    m = Model()
    mask = pd.Series([False] * 5 + [True] * 5)
    x = m.add_variables(coords=[range(10)], mask=mask)
    m.add_variables()
    m.add_constraints(x, EQUAL, 0)
    A = m.constraints.to_matrix(filter_missings=True)
    assert A.shape == (5, 6)
    assert A.shape == (m.ncons, m.nvars)

    A = m.constraints.to_matrix(filter_missings=False)
    assert A.shape == m.shape


def test_constraint_matrix_masked_constraints():
    """
    Test constraint matrix with missing constraints.
    """
    # now with missing variables
    m = Model()
    mask = pd.Series([False] * 5 + [True] * 5)
    x = m.add_variables(coords=[range(10)])
    m.add_variables()
    m.add_constraints(x, EQUAL, 0, mask=mask)
    A = m.constraints.to_matrix(filter_missings=True)
    assert A.shape == (5, 11)
    assert A.shape == (m.ncons, m.nvars)

    A = m.constraints.to_matrix(filter_missings=False)
    assert A.shape == m.shape


def test_constraint_matrix_masked_constraints_and_variables():
    """
    Test constraint matrix with missing constraints.
    """
    # now with missing variables
    m = Model()
    mask = pd.Series([False] * 5 + [True] * 5)
    x = m.add_variables(coords=[range(10)], mask=mask)
    m.add_variables()
    m.add_constraints(x, EQUAL, 0, mask=mask)
    A = m.constraints.to_matrix(filter_missings=True)
    assert A.shape == (5, 6)
    assert A.shape == (m.ncons, m.nvars)

    A = m.constraints.to_matrix(filter_missings=False)
    assert A.shape == m.shape


def test_get_name_by_label():
    m = Model()
    x = m.add_variables(coords=[range(10)])
    y = m.add_variables(coords=[range(10)])

    m.add_constraints(x + y <= 10, name="first")
    m.add_constraints(x - y >= 5, name="second")

    assert m.constraints.get_name_by_label(4) == "first"
    assert m.constraints.get_name_by_label(14) == "second"

    with pytest.raises(ValueError):
        m.constraints.get_name_by_label(30)

    with pytest.raises(ValueError):
        m.constraints.get_name_by_label("first")


def test_constraints_inequalities(m):
    assert isinstance(m.constraints.inequalities, linopy.constraints.Constraints)


def test_constraints_equalities(m):
    assert isinstance(m.constraints.equalities, linopy.constraints.Constraints)
