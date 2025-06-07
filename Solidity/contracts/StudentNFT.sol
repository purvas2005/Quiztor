// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "hardhat/console.sol";

contract StudentBadgeNFT is ERC721URIStorage, Ownable {
    uint256 private _tokenIds;

    //Basic details of the Badge in terms of how many are minted thus far and what is the Cap
    struct BadgeInfo {
        uint256 minted;
        uint256 cap;
    }

    //Map to store the Badge Type to the details of the Badge wrt how many are minted thus far and what is the Cap
    mapping(string => BadgeInfo) public badgeTypes;

    //The details of the Badges that are minted is stored in this structure
    event BadgeMinted(
        address indexed recipient,
        uint256 indexed tokenId,
        string badgeType,
        string metadataURI
    );

    constructor(
        address initialOwner
    ) ERC721("StudentBadgeNFT", "SBNFT") Ownable(initialOwner) {}

    /**
     * @dev Sets the maximum allowed number of badges for a specific badge type.
     * Can only be called by the owner.
     */
    function setBadgeCap(
        string memory badgeType,
        uint256 cap
    ) public onlyOwner {
        console.log("setBadgeCap", badgeType, cap);
        badgeTypes[badgeType].cap = cap;
    }

    /**
     * @dev Returns whether more badges of a specific type can be minted.
     */
    function canMintBadge(string memory badgeType) public view returns (bool) {
        return badgeTypes[badgeType].minted < badgeTypes[badgeType].cap;
    }

    /**
     * @dev Returns how many badges of a specific type have been minted.
     */
    function getMintedCount(
        string memory badgeType
    ) public view returns (uint256) {
        console.log("getMintedCount", badgeType);
        return badgeTypes[badgeType].minted;
    }

    /**
     * @dev Mints a badge NFT of a specific type to the recipient.
     * Only the owner can call this.
     */
    function mintBadge(
        address recipient,
        string memory badgeType,
        string memory tokenURI
    ) public onlyOwner returns (uint256) {
        require(
            canMintBadge(badgeType),
            "Minting limit reached for this badge"
        );

        _tokenIds += 1;
        uint256 newItemId = _tokenIds;

        _safeMint(recipient, newItemId);
        _setTokenURI(newItemId, tokenURI);

        badgeTypes[badgeType].minted += 1;

        console.log(
            "mintBadge Function",
            badgeType,
            badgeTypes[badgeType].minted
        );

        emit BadgeMinted(recipient, newItemId, badgeType, tokenURI);
        return newItemId;
    }

    function totalSupply() public view returns (uint256) {
        console.log("totalSupply() called");
        return _tokenIds;
    }
}
