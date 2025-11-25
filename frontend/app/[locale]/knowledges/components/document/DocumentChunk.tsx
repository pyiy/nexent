"use client";

import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  Tabs,
  Card,
  Badge,
  Button,
  App,
  Spin,
  Tag,
  Tooltip as AntdTooltip,
  Pagination,
  Input,
  Select,
} from "antd";
import {
  Download,
  ScanText,
  Trash2,
  SquarePen,
  Search,
  FilePlus2,
  Goal,
  X,
} from "lucide-react";
import { FieldNumberOutlined } from "@ant-design/icons";
import knowledgeBaseService from "@/services/knowledgeBaseService";
import { Document } from "@/types/knowledgeBase";
import log from "@/lib/logger";
import { formatScoreAsPercentage, getScoreColor } from "@/lib/utils";
import {
  Tooltip as UITooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
} from "@/components/ui/tooltip";

interface Chunk {
  id: string;
  content: string;
  path_or_url?: string;
  filename?: string;
  create_time?: string;
  score?: number; // Search score (0-1 range) - only present in search results
}

interface DocumentChunkProps {
  knowledgeBaseName: string;
  documents: Document[];
  getFileIcon: (type: string) => string;
  currentEmbeddingModel?: string | null;
  knowledgeBaseEmbeddingModel?: string;
}

const PAGE_SIZE = 10;

const TABS_ROOT_CLASS = "document-chunk-tabs";

const DocumentChunk: React.FC<DocumentChunkProps> = ({
  knowledgeBaseName,
  documents,
  getFileIcon,
  currentEmbeddingModel = null,
  knowledgeBaseEmbeddingModel = "",
}) => {
  const { t } = useTranslation();
  const { message } = App.useApp();
  const [chunks, setChunks] = useState<Chunk[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState(false);
  const [activeDocumentKey, setActiveDocumentKey] = useState<string>("");
  const [documentChunkCounts, setDocumentChunkCounts] = useState<
    Record<string, number>
  >({});
  const [pagination, setPagination] = useState<{
    page: number;
    pageSize: number;
  }>({
    page: 1,
    pageSize: PAGE_SIZE,
  });
  const [searchType, setSearchType] = useState<"document" | "chunk">("chunk");
  const [searchValue, setSearchValue] = useState<string>("");
  const [filteredDocumentIds, setFilteredDocumentIds] = useState<
    string[] | null
  >(null);
  const [chunkSearchResult, setChunkSearchResult] = useState<Chunk[] | null>(
    null
  );
  const [chunkSearchTotal, setChunkSearchTotal] = useState<number>(0);
  const [chunkSearchLoading, setChunkSearchLoading] = useState(false);

  const resetChunkSearch = React.useCallback(() => {
    setChunkSearchResult(null);
    setChunkSearchTotal(0);
    setChunkSearchLoading(false);
  }, []);

  const displayedDocuments = React.useMemo(() => {
    if (filteredDocumentIds === null) {
      return documents;
    }
    return documents.filter((doc) => filteredDocumentIds.includes(doc.id));
  }, [documents, filteredDocumentIds]);

  const isChunkSearchActive = chunkSearchResult !== null;

  // Determine if in read-only mode
  const isReadOnlyMode = React.useMemo(() => {
    if (!currentEmbeddingModel || !knowledgeBaseEmbeddingModel) {
      return false;
    }
    if (knowledgeBaseEmbeddingModel === "unknown") {
      return false;
    }
    return currentEmbeddingModel !== knowledgeBaseEmbeddingModel;
  }, [currentEmbeddingModel, knowledgeBaseEmbeddingModel]);

  // Set active document when documents change
  useEffect(() => {
    const sourceDocuments =
      filteredDocumentIds !== null ? displayedDocuments : documents;

    if (sourceDocuments.length === 0) {
      if (activeDocumentKey) {
        setActiveDocumentKey("");
      }
      setChunks([]);
      setTotal(0);
      return;
    }

    const hasActiveDocument = sourceDocuments.some(
      (doc) => doc.id === activeDocumentKey
    );

    if (!hasActiveDocument) {
      setActiveDocumentKey(sourceDocuments[0].id);
      setPagination((prev) => ({ ...prev, page: 1 }));
    }
  }, [documents, displayedDocuments, filteredDocumentIds, activeDocumentKey]);

  // Load chunks for active document with server-side pagination
  useEffect(() => {
    const loadChunks = async () => {
      if (!knowledgeBaseName || !activeDocumentKey) {
        return;
      }

      setLoading(true);
      try {
        const result = await knowledgeBaseService.previewChunksPaginated(
          knowledgeBaseName,
          pagination.page,
          pagination.pageSize,
          activeDocumentKey
        );

        setChunks(result.chunks || []);
        setTotal(result.total || 0);
        setDocumentChunkCounts((prev) => ({
          ...prev,
          [activeDocumentKey]: result.total || 0,
        }));
      } catch (error) {
        log.error("Failed to load chunks:", error);
        message.error(t("document.chunk.error.loadFailed"));
      } finally {
        setLoading(false);
      }
    };

    loadChunks();
  }, [
    knowledgeBaseName,
    activeDocumentKey,
    pagination.page,
    pagination.pageSize,
    message,
    t,
  ]);

  useEffect(() => {
    if (documents.length === 0) {
      setDocumentChunkCounts({});
      setActiveDocumentKey("");
      return;
    }

    setDocumentChunkCounts((prev) => {
      const next = { ...prev };
      const docIds = new Set<string>();

      documents.forEach((doc) => {
        docIds.add(doc.id);

        if (
          typeof doc.chunk_num === "number" &&
          doc.chunk_num >= 0 &&
          next[doc.id] !== doc.chunk_num
        ) {
          next[doc.id] = doc.chunk_num;
        }
      });

      Object.keys(next).forEach((docId) => {
        if (!docIds.has(docId)) {
          delete next[docId];
        }
      });

      return next;
    });
  }, [documents]);

  // Handle document tab change
  const handleTabChange = (key: string) => {
    setActiveDocumentKey(key);
    setChunks([]);
    setTotal(documentChunkCounts[key] ?? 0);
    setPagination((prev) => ({ ...prev, page: 1 }));
    resetChunkSearch();
  };

  // Handle pagination change
  const handlePaginationChange = (page: number, pageSize: number) => {
    setPagination({ page, pageSize });
  };

  const getDisplayName = React.useCallback((name: string): string => {
    const lastDotIndex = name.lastIndexOf(".");
    if (lastDotIndex <= 0) {
      return name;
    }
    return name.substring(0, lastDotIndex);
  }, []);

  // Clear search input and reset all search states
  const handleClearSearch = React.useCallback(() => {
    setSearchValue("");
    setFilteredDocumentIds(null);
    resetChunkSearch();
  }, [resetChunkSearch]);

  const handleSearch = React.useCallback(async () => {
    const trimmedValue = searchValue.trim();

    if (!trimmedValue) {
      setFilteredDocumentIds(null);
      resetChunkSearch();
      return;
    }

    if (searchType === "document") {
      resetChunkSearch();
      const searchLower = trimmedValue.toLowerCase();
      const matchedDocs = documents.filter((doc) => {
        const fullName = (doc.name || "").trim();
        const displayName = getDisplayName(fullName);
        return (
          fullName.toLowerCase().includes(searchLower) ||
          displayName.toLowerCase().includes(searchLower)
        );
      });

      if (matchedDocs.length === 0) {
        setFilteredDocumentIds([]);
        setActiveDocumentKey("");
        setChunks([]);
        setTotal(0);
        message.warning(t("document.chunk.search.noDocument"));
        return;
      }

      setFilteredDocumentIds(matchedDocs.map((doc) => doc.id));

      const hasActive = matchedDocs.some((doc) => doc.id === activeDocumentKey);

      if (!hasActive) {
        setActiveDocumentKey(matchedDocs[0].id);
        setPagination((prev) => ({ ...prev, page: 1 }));
      }
      return;
    }

    if (!activeDocumentKey) {
      message.warning(t("document.chunk.search.noActiveDocument"));
      return;
    }

    if (!knowledgeBaseName) {
      message.error(t("document.chunk.error.searchFailed"));
      return;
    }

    setFilteredDocumentIds(null);
    setChunkSearchResult([]);
    setChunkSearchTotal(0);
    setChunkSearchLoading(true);

    try {
      const response = await knowledgeBaseService.hybridSearch(
        knowledgeBaseName,
        trimmedValue,
        {
          topK: pagination.pageSize,
        }
      );

      const filteredChunks = (response.results || [])
        .map((item) => {
          // Backend returns document fields at the top level
          return {
            id: item.id || "",
            content: item.content || "",
            path_or_url: item.path_or_url,
            filename: item.filename,
            create_time: item.create_time,
            score: item.score, // Preserve search score for display
          };
        })
        .filter((chunk) => chunk.path_or_url === activeDocumentKey);

      setChunkSearchResult(filteredChunks);
      setChunkSearchTotal(filteredChunks.length);

      if (filteredChunks.length === 0) {
        message.info(t("document.chunk.search.noChunk"));
      }
    } catch (error) {
      log.error("Failed to search chunks:", error);
      message.error(t("document.chunk.error.searchFailed"));
      resetChunkSearch();
    } finally {
      setChunkSearchLoading(false);
    }
  }, [
    activeDocumentKey,
    documents,
    getDisplayName,
    knowledgeBaseName,
    message,
    pagination.pageSize,
    resetChunkSearch,
    searchType,
    searchValue,
    t,
  ]);

  // Download chunk as txt file
  const handleDownloadChunk = (chunk: Chunk) => {
    try {
      const content = chunk.content || "";
      const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${chunk.id}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      log.error("Failed to download chunk:", error);
      message.error(t("document.chunk.error.downloadFailed"));
    }
  };

  const renderDocumentLabel = (doc: Document, chunkCount: number) => {
    const displayName = getDisplayName(doc.name || "");

    return (
      <AntdTooltip title={displayName} placement="top" arrow>
        <div className="flex w-full items-center justify-between gap-2 min-w-0">
          <div className="flex items-center gap-1.5 min-w-0">
            <span>{getFileIcon(doc.type)}</span>
            <span className="truncate text-sm font-medium text-gray-800 max-w-[150px]">
              {displayName}
            </span>
          </div>
          <Badge
            color="#1677ff"
            showZero
            count={chunkCount}
            className="flex-shrink-0 chunk-count-badge"
          />
        </div>
      </AntdTooltip>
    );
  };

  const tabItems = displayedDocuments.map((doc) => {
    const chunkCount = documentChunkCounts[doc.id] ?? doc.chunk_num ?? 0;
    const isActive = doc.id === activeDocumentKey;
    const docChunksData = isActive
      ? isChunkSearchActive
        ? {
            chunks: chunkSearchResult ?? [],
            total: chunkSearchTotal,
            paginatedChunks: chunkSearchResult ?? [],
          }
        : { chunks, total, paginatedChunks: chunks }
      : { chunks: [], total: 0, paginatedChunks: [] };

    const showLoadingState = isActive
      ? isChunkSearchActive
        ? chunkSearchLoading && docChunksData.paginatedChunks.length === 0
        : loading && docChunksData.paginatedChunks.length === 0
      : false;

    return {
      key: doc.id,
      label: renderDocumentLabel(doc, chunkCount),
      children: (
        <div className="flex h-full flex-col min-h-0 overflow-hidden">
          <div className="flex-1 min-h-0 overflow-y-auto p-4 pb-8">
            {showLoadingState ? (
              <div className="flex h-52 items-center justify-center">
                <Spin size="large" />
              </div>
            ) : docChunksData.total === 0 ? (
              <div className="rounded-md border border-dashed border-gray-200 p-10 text-center text-sm text-gray-500">
                {t("document.chunk.noChunks")}
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {docChunksData.paginatedChunks.map((chunk, index) => (
                  <Card
                    key={chunk.id || index}
                    size="small"
                    className="w-full"
                    title={
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex flex-wrap gap-1">
                          <Tag className="inline-flex items-center px-1.5 py-0.5 text-xs font-medium bg-gray-200 text-gray-800 border border-gray-200 rounded-md">
                            <FieldNumberOutlined className="text-[12px]" />
                            <span>
                              {(pagination.page - 1) * pagination.pageSize +
                                index +
                                1}
                            </span>
                          </Tag>
                          <Tag className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium bg-gray-200 text-gray-800 border border-gray-200 rounded-md">
                            <ScanText size={14} />
                            <span>
                              {t("document.chunk.characterCount", {
                                count: (chunk.content || "").length,
                              })}
                            </span>
                          </Tag>
                          {chunk.score !== undefined && (
                            <Tag
                              className="inline-flex items-center gap-1 px-1.5 py-0.5 text-xs font-medium border rounded-md"
                              style={{
                                backgroundColor: getScoreColor(chunk.score),
                                color: "#fff",
                                borderColor: getScoreColor(chunk.score),
                              }}
                            >
                              <Goal size={14} />
                              <span>
                                {formatScoreAsPercentage(chunk.score)}
                              </span>
                            </Tag>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          {!isReadOnlyMode && (
                            <UITooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  type="text"
                                  icon={<SquarePen size={16} />}
                                  onClick={() => {
                                    // TODO: Implement edit functionality
                                  }}
                                  size="small"
                                  className="self-center"
                                />
                              </TooltipTrigger>
                              <TooltipContent className="font-normal">
                                {t("document.chunk.tooltip.edit")}
                              </TooltipContent>
                            </UITooltip>
                          )}
                          <UITooltip>
                            <TooltipTrigger asChild>
                              <Button
                                type="text"
                                icon={<Download size={16} />}
                                onClick={() => handleDownloadChunk(chunk)}
                                size="small"
                                className="self-center"
                              />
                            </TooltipTrigger>
                            <TooltipContent className="font-normal">
                              {t("document.chunk.tooltip.download")}
                            </TooltipContent>
                          </UITooltip>
                          <UITooltip>
                            <TooltipTrigger asChild>
                              <Button
                                type="text"
                                danger
                                icon={<Trash2 size={16} />}
                                onClick={() => {
                                  // TODO: Implement delete functionality
                                }}
                                size="small"
                                className="self-center"
                              />
                            </TooltipTrigger>
                            <TooltipContent className="font-normal">
                              {t("document.chunk.tooltip.delete")}
                            </TooltipContent>
                          </UITooltip>
                        </div>
                      </div>
                    }
                  >
                    <div className="max-h-[150px] overflow-y-auto break-words whitespace-pre-wrap text-sm">
                      {chunk.content || ""}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </div>
      ),
    };
  });

  if (!isChunkSearchActive && loading && chunks.length === 0) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <Spin size="large" />
      </div>
    );
  }

  const activeDocumentTotal = isChunkSearchActive
    ? chunkSearchTotal
    : documentChunkCounts[activeDocumentKey] ?? total ?? 0;
  const shouldShowPagination = !isChunkSearchActive && activeDocumentTotal > 0;

  return (
    <TooltipProvider>
      <div className="flex h-full w-full flex-col min-h-0 overflow-hidden">
        {/* Search and Add Button Bar */}
        <div className="flex items-center justify-end gap-2 px-2 py-3 border-b border-gray-200 shrink-0">
          <div className="flex items-center gap-2">
            <Input
              placeholder={t("document.chunk.search.placeholder")}
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onPressEnter={() => {
                void handleSearch();
              }}
              style={{ width: 320 }}
              addonBefore={
                <Select
                  value={searchType}
                  onChange={setSearchType}
                  variant="borderless"
                  style={{ width: 85 }}
                  options={[
                    {
                      label: t("document.chunk.search.chunk"),
                      value: "chunk",
                    },
                    {
                      label: t("document.chunk.search.document"),
                      value: "document",
                    },
                  ]}
                  popupMatchSelectWidth={false}
                />
              }
              suffix={
                <div className="flex items-center gap-1">
                  {searchValue && (
                    <Button
                      type="text"
                      icon={<X size={16} />}
                      onClick={handleClearSearch}
                      size="small"
                      className="text-gray-500 hover:text-gray-700"
                    />
                  )}
                  <Button
                    type="text"
                    icon={<Search size={16} />}
                    onClick={() => {
                      void handleSearch();
                    }}
                    size="small"
                    loading={
                      searchType === "chunk" ? chunkSearchLoading : false
                    }
                  />
                </div>
              }
            />
          </div>
          {!isReadOnlyMode && (
            <UITooltip>
              <TooltipTrigger asChild>
                <Button
                  type="text"
                  icon={<FilePlus2 size={16} />}
                  onClick={() => {
                    // TODO: Implement add functionality
                  }}
                ></Button>
              </TooltipTrigger>
              <TooltipContent className="font-normal">
                {t("document.chunk.tooltip.create")}
              </TooltipContent>
            </UITooltip>
          )}
        </div>

        <Tabs
          tabPosition="left"
          activeKey={activeDocumentKey}
          onChange={handleTabChange}
          items={tabItems}
          className={`h-full w-full min-h-0 ${TABS_ROOT_CLASS}`}
          rootClassName="h-full"
        />
        {shouldShowPagination && (
          <div className="sticky bottom-0 left-0 z-10 flex w-full justify-center bg-white px-8 pb-4 pt-2 shadow-[0_-4px_12px_rgba(15,23,42,0.04)]">
            <Pagination
              current={pagination.page}
              pageSize={pagination.pageSize}
              total={activeDocumentTotal}
              onChange={handlePaginationChange}
              disabled={loading}
              showQuickJumper
              showTotal={(pageTotal, range) =>
                t("document.chunk.pagination.range", {
                  defaultValue: "{{start}}-{{end}} of {{total}}",
                  start: range[0],
                  end: range[1],
                  total: pageTotal,
                })
              }
            />
          </div>
        )}
      </div>
    </TooltipProvider>
  );
};

export default DocumentChunk;

