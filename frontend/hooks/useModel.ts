'use client';

import { useEffect } from 'react';
import { ModelType } from '@/types/config';
import { modelService } from '@/services/modelService';

interface UseModelProps {
  form: {
    type: ModelType;
    isBatchImport: boolean;
    apiKey: string;
    provider: string;
    isMultimodal: boolean;
  };
  setModelList: (models: any[]) => void;
  setSelectedModelIds: (ids: Set<string>) => void;
  setShowModelList: (show: boolean) => void;
  setLoadingModelList: (loading: boolean) => void;
  message: any;
  t: (key: string, options?: any) => string;
}

export function useModel({
  form,
  setModelList,
  setSelectedModelIds,
  setShowModelList,
  setLoadingModelList,
  message,
  t
}: UseModelProps) {
  
  const getModelList = async () => {
    setShowModelList(true);
    setLoadingModelList(true);
    const modelType = form.type === "embedding" && form.isMultimodal ? 
        "multi_embedding" as ModelType : 
        form.type;
    try {
      const result = await modelService.addProviderModel({
        provider: form.provider,
        type: modelType,
        apiKey: form.apiKey.trim() === "" ? "sk-no-api-key" : form.apiKey
      });
      setModelList(result);
      if (!result || result.length === 0) {
        message.error(t('model.dialog.error.noModelsFetched'));
      }
      const selectedModels = await getProviderSelectedModalList() || [];
      // 关键逻辑
      if (!selectedModels.length) {
        // 全部不选
        setSelectedModelIds(new Set());
      } else {
        // 只选中 selectedModels
        setSelectedModelIds(new Set(selectedModels.map((m: any) => m.id)));
      }
    } catch (error) {
      message.error(t('model.dialog.error.addFailed', { error }));
      console.error(t('model.dialog.error.addFailedLog'), error);
    } finally {
      setLoadingModelList(false);
    }
  };

  const getProviderSelectedModalList = async () => {
    const modelType = form.type === "embedding" && form.isMultimodal ? 
        "multi_embedding" as ModelType : 
        form.type;
    const result = await modelService.getProviderSelectedModalList({
      provider: form.provider,
      type: modelType,
      api_key: form.apiKey.trim() === "" ? "sk-no-api-key" : form.apiKey
    });
    return result;
  };

  // useEffect to automatically fetch model list when conditions are met
  useEffect(() => {
    if (form.isBatchImport && form.apiKey.trim() !== "") {
      getModelList();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.type, form.isBatchImport]);

  return {
    getModelList,
    getProviderSelectedModalList
  };
}
