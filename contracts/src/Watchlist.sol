// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title PulseBNB Watchlist
 * @notice Free, permissionless on-chain watchlist for BNB Chain builders.
 *         Anyone can watch/unwatch any target. No owner, no fees, no token.
 * @dev BNB Hack: Online Edition, June 2026. pulsebnb-web.vercel.app
 */
contract Watchlist {
    event Watched(address indexed watcher, address indexed target, uint256 timestamp);
    event Unwatched(address indexed watcher, address indexed target, uint256 timestamp);

    mapping(address => mapping(address => bool)) public isWatching;
    mapping(address => uint256) public watcherCount;
    uint256 public totalWatches;

    function watch(address target) external {
        require(target != address(0), "zero target");
        require(!isWatching[msg.sender][target], "already watching");
        isWatching[msg.sender][target] = true;
        watcherCount[target] += 1;
        totalWatches += 1;
        emit Watched(msg.sender, target, block.timestamp);
    }

    function unwatch(address target) external {
        require(isWatching[msg.sender][target], "not watching");
        isWatching[msg.sender][target] = false;
        watcherCount[target] -= 1;
        emit Unwatched(msg.sender, target, block.timestamp);
    }

    function watchMany(address[] calldata targets) external {
        for (uint256 i = 0; i < targets.length; i++) {
            address t = targets[i];
            if (t != address(0) && !isWatching[msg.sender][t]) {
                isWatching[msg.sender][t] = true;
                watcherCount[t] += 1;
                totalWatches += 1;
                emit Watched(msg.sender, t, block.timestamp);
            }
        }
    }
}
