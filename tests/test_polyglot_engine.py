# -*- coding: utf-8 -*-
"""Unit tests for Universal Polyglot AST Engine (tzero_polyglot.py)."""

import unittest
from tzero_polyglot import PolyglotTokenReducer


class TestPolyglotEngine(unittest.TestCase):
    def test_rust_reduction(self):
        code = """use std::collections::HashMap;

pub struct State {
    count: usize,
    items: Vec<String>,
}

impl State {
    pub fn new() -> Self {
        let mut map = HashMap::new();
        map.insert("key", 42);
        State { count: 0, items: Vec::new() }
    }

    pub async fn process_data(&self, input: &str) -> Result<usize, String> {
        let trimmed = input.trim();
        println!("Logging: {}", trimmed);
        Ok(trimmed.len())
    }
}
"""
        res = PolyglotTokenReducer.reduce_code(code, "lib.rs")
        self.assertIn("use std::collections::HashMap;", res)
        self.assertIn("pub struct State", res)
        self.assertIn("pub fn new() -> Self", res)
        self.assertIn("pub async fn process_data(&self, input: &str) -> Result<usize, String>", res)
        self.assertNotIn("println!(\"Logging: {}\", trimmed);", res)

    def test_go_reduction(self):
        code = """package main

import (
    "fmt"
    "io"
)

type Worker interface {
    Process(data string) error
}

func HandleTask(w Worker, data string) error {
    if data == "" {
        return fmt.Errorf("empty data")
    }
    return w.Process(data)
}
"""
        res = PolyglotTokenReducer.reduce_code(code, "main.go")
        self.assertIn("package main", res)
        self.assertIn("type Worker interface", res)
        self.assertIn("func HandleTask(w Worker, data string) error", res)
        self.assertNotIn("fmt.Errorf", res)

    def test_solidity_reduction(self):
        code = """pragma solidity ^0.8.20;

contract Vault {
    mapping(address => uint256) public balances;
    event Deposit(address indexed sender, uint256 amount);

    function deposit() external payable {
        require(msg.value > 0, "Zero amount");
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }
}
"""
        res = PolyglotTokenReducer.reduce_code(code, "Vault.sol")
        self.assertIn("pragma solidity", res)
        self.assertIn("contract Vault", res)
        self.assertIn("event Deposit", res)
        self.assertIn("function deposit() external payable", res)
        self.assertNotIn("balances[msg.sender] += msg.value", res)

    def test_cpp_reduction(self):
        code = """#include <iostream>
#include <vector>

class Engine {
public:
    void Start() {
        std::cout << "Starting..." << std::endl;
        init_hardware();
    }
};
"""
        res = PolyglotTokenReducer.reduce_code(code, "engine.cpp")
        self.assertIn("#include <iostream>", res)
        self.assertIn("class Engine", res)
        self.assertIn("void Start()", res)
        self.assertNotIn("init_hardware", res)

    def test_ruby_reduction(self):
        code = """require 'json'
require_relative 'config'

class PaymentGateway
    include Loggable
    attr_reader :api_key

    def process(amount)
        do_heavy_crypto(amount)
        return true
    end
end
"""
        res = PolyglotTokenReducer.reduce_code(code, "gateway.rb")
        self.assertIn("require 'json'", res)
        self.assertIn("class PaymentGateway", res)
        self.assertIn("attr_reader :api_key", res)
        self.assertIn("def process(amount)", res)
        self.assertNotIn("do_heavy_crypto", res)

    def test_php_reduction(self):
        code = """<?php
namespace App\\Services;
use App\\Models\\User;

class UserService {
    public function findUser(int $id): ?User {
        $raw = $this->db->query("SELECT * FROM users");
        return new User($raw);
    }
}
"""
        res = PolyglotTokenReducer.reduce_code(code, "UserService.php")
        self.assertIn("<?php", res)
        self.assertIn("namespace App\\Services;", res)
        self.assertIn("class UserService", res)
        self.assertIn("public function findUser", res)
        self.assertNotIn("SELECT * FROM users", res)

    def test_swift_reduction(self):
        code = """import Foundation

protocol DataStore {
    func save(key: String) -> Bool
}

class CloudManager {
    func sync() {
        let backgroundQueue = DispatchQueue.global()
        backgroundQueue.async { print("syncing") }
    }
}
"""
        res = PolyglotTokenReducer.reduce_code(code, "CloudManager.swift")
        self.assertIn("import Foundation", res)
        self.assertIn("protocol DataStore", res)
        self.assertIn("class CloudManager", res)
        self.assertIn("func sync()", res)
        self.assertNotIn("DispatchQueue.global()", res)

    def test_kotlin_reduction(self):
        code = """package com.example.service

import kotlinx.coroutines.flow.Flow

class UserService {
    fun getUser(id: String): String {
        val entity = repo.find(id)
        return entity.name
    }
}
"""
        res = PolyglotTokenReducer.reduce_code(code, "UserService.kt")
        self.assertIn("package com.example.service", res)
        self.assertIn("class UserService", res)
        self.assertIn("fun getUser", res)
        self.assertNotIn("repo.find(id)", res)

    def test_dart_reduction(self):
        code = """import 'package:flutter/material.dart';

class CustomCard {
    Widget build(BuildContext context) {
        return Container(child: Text("Hello"));
    }
}
"""
        res = PolyglotTokenReducer.reduce_code(code, "card.dart")
        self.assertIn("import 'package:flutter/material.dart';", res)
        self.assertIn("class CustomCard", res)
        self.assertIn("Widget build(BuildContext context)", res)
        self.assertNotIn("Container(child: Text", res)


if __name__ == "__main__":
    unittest.main()

