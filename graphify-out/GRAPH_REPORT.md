# Graph Report - .  (2026-05-06)

## Corpus Check
- 258 files · ~967,339 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3519 nodes · 6960 edges · 108 communities detected
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 1191 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `BlockType` - 169 edges
2. `oMath2Latex` - 138 edges
3. `ContentType` - 100 edges
4. `Script` - 63 edges
5. `Formatting` - 61 edges
6. `DocxConverter` - 60 edges
7. `PptxConverter` - 56 edges
8. `UnimerMBartConfig` - 48 edges
9. `XlsxConverter` - 47 edges
10. `DonutSwinModelOutput` - 45 edges

## Surprising Connections (you probably didn't know these)
- `Assign task-local unique stems while preserving input order.` --uses--> `MakeMode`  [INFERRED]
  mineru\mineru\cli\common.py → mineru\mineru\utils\enum_class.py
- `清理代码内容，移除Markdown代码块的开始和结束标记` --uses--> `BlockType`  [INFERRED]
  mineru\mineru\utils\visual_magic_model_utils.py → mineru\mineru\utils\enum_class.py
- `将纵向文本的spans合并成纵向lines（从右向左阅读）` --uses--> `ContentType`  [INFERRED]
  mineru\mineru\utils\span_block_fix.py → mineru\mineru\utils\enum_class.py
- `根据显存大小或环境变量获取 batch ratio` --uses--> `HybridModelSingleton`  [INFERRED]
  mineru\mineru\backend\hybrid\hybrid_analyze.py → mineru\mineru\backend\pipeline\model_init.py
- `根据显存大小或环境变量获取 batch ratio` --uses--> `ModelSingleton`  [INFERRED]
  mineru\mineru\backend\hybrid\hybrid_analyze.py → mineru\mineru\backend\vlm\vlm_analyze.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.02
Nodes (162): BaseModel, DocxConverter, _format_text_with_hyperlink(), _get_format_from_run(), _get_paragraph_text_from_contents(), _get_style_str_from_format(), _has_visible_style(), _is_hidden_run() (+154 more)

### Community 1 - "Community 1"
Cohesion: 0.02
Nodes (119): Dataset, ModelPath, LayoutLMv3TextEmbeddings, convert_binary(), convert_path(), count_table_cells_physical(), escape_html(), PaddleTable (+111 more)

### Community 2 - "Community 2"
Cohesion: 0.02
Nodes (85): Activation, aio_do_parse(), _async_process_hybrid(), _async_process_vlm(), build_hybrid_dependency_error_message(), build_task_stem_candidate(), convert_pdf_bytes_to_bytes(), do_parse() (+77 more)

### Community 3 - "Community 3"
Cohesion: 0.03
Nodes (80): list, MBartDecoder, MBartForCausalLM, AttentionMaskConverter, CustomMBartDecoder, CustomMBartForCausalLM, generate(), generate_export() (+72 more)

### Community 4 - "Community 4"
Cohesion: 0.03
Nodes (54): CausalLMOutputWithCrossAttentions, r"""     This is the configuration class to store the configuration of a [`MBar, UnimerMBartConfig, GenerationMixin, create_operators(), Textual TUI for local MinerU batch runs., create operators based on the config     Args:         params(list): a dict li, CausalLMOutputWithCrossAttentionsAndCounting (+46 more)

### Community 5 - "Community 5"
Cohesion: 0.04
Nodes (82): _build_bar(), build_http_timeout(), _build_render_line_locked(), build_request_form_data(), build_task_execution_progress(), build_visualization_jobs(), collect_input_documents(), create_live_task_status_renderer() (+74 more)

### Community 6 - "Community 6"
Cohesion: 0.03
Nodes (58): OrderedDict, DonutSwinEncoderOutput, DonutSwinModelOutput, Convert self to a tuple containing all the attributes/keys that are not `None`., Convert self to a tuple containing all the attributes/keys that are not `None`., BNAndPad, conv_bn(), ConvBNAct (+50 more)

### Community 7 - "Community 7"
Cohesion: 0.05
Nodes (55): ABC, DataReader, DataWriter, IOReader, IOWriter, Write the data to file, the data will be encoded to bytes.          Args:, Read the file.          Args:             path (str): file path to read, read_at() (+47 more)

### Community 8 - "Community 8"
Cohesion: 0.03
Nodes (62): check_img_bbox(), cut_image_and_table(), cal_canvas_rect(), draw_bbox_with_number(), draw_bbox_without_number(), draw_layout_bbox(), draw_span_bbox(), Enum (+54 more)

### Community 9 - "Community 9"
Cohesion: 0.04
Nodes (43): r"""     This is the configuration class to store the configuration of a [`Unim, UnimerSwinConfig, ConvEnhance, drop_path(), forward(), Prunes heads of the model. heads_to_prune: dict of {layer_num: list of heads to, r"""         bool_masked_pos (`torch.BoolTensor` of shape `(batch_size, num_pat, Partitions the given input into windows. (+35 more)

### Community 10 - "Community 10"
Cohesion: 0.06
Nodes (85): ContentTypeV2, MakeMode, _append_hyperlink_part(), _append_text_part(), _apply_configured_style(), _apply_html_style(), _apply_markdown_style(), _build_media_path() (+77 more)

### Community 11 - "Community 11"
Cohesion: 0.05
Nodes (30): _bbox_area(), _bbox_intersection(), _bytes_to_data_uri(), _cleanup_slide_text_block_metadata(), _find_first_embedded_image_rid(), _format_text_with_hyperlink(), _get_run_raw_text(), _group_shape_transform() (+22 more)

### Community 12 - "Community 12"
Cohesion: 0.04
Nodes (69): _backup_file(), BM25, _copy_file_safely(), detect_domain(), ensure_rule_file(), _ensure_within(), _import_search_core(), _iter_markdown_sections() (+61 more)

### Community 13 - "Community 13"
Cohesion: 0.04
Nodes (59): # TODO: rewrite tokenizer, TokenizerWrapper, UnimernetModel, _add_engine_kwarg_if_missing(), _add_server_arg_if_missing(), _add_server_flag_if_missing(), _apply_engine_config(), _apply_server_config() (+51 more)

### Community 14 - "Community 14"
Cohesion: 0.06
Nodes (43): load_parse_inputs(), build_sync_router_task_result_response(), build_sync_task_headers(), build_upload_destination(), cleanup_path(), cleanup_temporary_directory(), create_app(), detect_visible_cuda_devices() (+35 more)

### Community 15 - "Community 15"
Cohesion: 0.04
Nodes (28): AttnLabelDecode, BaseRecLabelDecode, CANLabelDecode, CTCLabelDecode, NRTRLabelDecode, convert text-index into text-label., Convert between text-label and text-index, Convert between text-label and text-index (+20 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (52): AsyncParseTask, AsyncTaskManager, build_result_dict(), build_result_response(), build_sync_file_parse_response(), build_task_submission_response(), build_upload_destination(), build_zip_arcname() (+44 more)

### Community 17 - "Community 17"
Cohesion: 0.04
Nodes (28): ClsPostProcess, Convert between text-label and text-index, DBPostProcess, box_score_fast: use bbox mean score as the mean score, The post process for Differentiable Binarization (DB)., box_score_slow: use polyon mean score as the mean score, _bitmap: single map with shape (1, H, W),             whose values are binarize, _bitmap: single map with shape (1, H, W),                 whose values are bina (+20 more)

### Community 18 - "Community 18"
Cohesion: 0.04
Nodes (38): FormulaRecognizer, _item_to_bbox(), _normalize_bbox(), LatexImageFormat, Resizes the image to the specified size.          Args:             img (PIL., Decodes the image by cropping margins, resizing, and adding padding., Calls the img_decode method on a list of images.          Args:             i, A class for transforming images according to UniMERNet test specifications. (+30 more)

### Community 19 - "Community 19"
Cohesion: 0.04
Nodes (29): DonutSwinAttention, DonutSwinConfig, DonutSwinDropPath, DonutSwinEmbeddings, DonutSwinEncoder, DonutSwinIntermediate, DonutSwinLayer, DonutSwinModel (+21 more)

### Community 20 - "Community 20"
Cohesion: 0.05
Nodes (18): BaseModel, the module for OCR.         args:             config (dict): the super paramet, BaseOCRV20, BaseOCRV20, TextClassifier, 对相同尺寸的图像进行批处理              Args:                 img_list: 相同尺寸的图像列表, 批处理预测方法，支持多张图像同时检测          Args:             img_list: 图像列表             max, reference from: https://github.com/jrosebr1/imutils/blob/master/imutils/perspect (+10 more)

### Community 21 - "Community 21"
Cohesion: 0.08
Nodes (10): _apply_inline_font_tags(), _contains_block_level_html(), _count_max_consecutive_true(), _escape_text_with_line_breaks(), _get_cell_hyperlink_target(), _get_sheet_content_layer(), _is_real_singleton_table(), _sanitize_hyperlink_target() (+2 more)

### Community 22 - "Community 22"
Cohesion: 0.08
Nodes (52): SplitFlag, adjust_table_rows_colspan(), _apply_cell_merge(), _build_front_cache(), _build_row_signature(), build_table_occupied_matrix(), _build_table_state(), build_table_state_from_html() (+44 more)

### Community 23 - "Community 23"
Cohesion: 0.07
Nodes (36): append_page_blocks_to_middle_json(), blocks_to_page_info(), _collect_index_text_blocks(), _extract_section_parts_from_content(), finalize_middle_json(), init_middle_json(), _link_index_entries_by_anchor(), Try to extract a leading section number (e.g. '1.2.1') from title content. (+28 more)

### Community 24 - "Community 24"
Cohesion: 0.07
Nodes (36): build_http_timeout(), _build_local_api_server_cli_args(), _build_local_api_server_env(), build_managed_process_popen_kwargs(), build_result_download_timeout(), cleanup_process_tree_descendants(), cleanup_process_tree_descendants_by_pid(), _cli_args_include_flag() (+28 more)

### Community 25 - "Community 25"
Cohesion: 0.07
Nodes (42): _apply_mask_boxes_to_image(), BatchAnalyze, _bbox_center(), _bbox_intersection(), _bbox_intersection_area(), _bbox_to_quad(), _bbox_to_relative_bbox(), _encode_table_inline_image() (+34 more)

### Community 26 - "Community 26"
Cohesion: 0.07
Nodes (45): classify_task_type(), _contains_any(), _extract_handoff_block(), _has_header(), _iter_jsonl(), load_cases(), _match_routing_signals(), _norm_prompt() (+37 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (44): _chart_uses_date_1904(), ChartSpec, _collect_plot_elements(), _excel_serial_to_iso(), _extract_cache_points(), extract_chart_html_from_ooxml(), _extract_multilevel_string_cache(), _extract_reference_cache() (+36 more)

### Community 28 - "Community 28"
Cohesion: 0.07
Nodes (36): adjust_lines(), affine_transform(), calculate_center_rotate_angle(), draw_lines(), final_adjust_lines(), fit_line(), get_3rd_point(), get_affine_transform() (+28 more)

### Community 29 - "Community 29"
Cohesion: 0.09
Nodes (21): _fmt_mmss(), _fmt_size(), MineruTUIApp, _pages_cell(), _short_name(), _tilde_path(), _digest_path(), _entry_for_new_file() (+13 more)

### Community 30 - "Community 30"
Cohesion: 0.08
Nodes (30): format_results(), main(), BM25, load_rule_map_rows(), load_skill_finder_rows(), non_frontend_specialist_ids(), parse_registry_agents(), read_csv_rows() (+22 more)

### Community 31 - "Community 31"
Cohesion: 0.1
Nodes (7): CropByPolys, SortPolyBoxes, AutoRectifier, CurveTextRectifier, get_rotate_crop_image(), Homography(), PlanB

### Community 32 - "Community 32"
Cohesion: 0.16
Nodes (31): _build_bbox(), _collect_text_for_lang_detection(), escape_special_markdown_char(), _format_embedded_html(), get_blocks_in_index_order(), _get_body_data(), _get_ref_text_item_blocks(), _get_seal_span() (+23 more)

### Community 33 - "Community 33"
Cohesion: 0.09
Nodes (31): _add_missing_known_namespaces(), _drop_blank_underline_value(), _is_skippable_corrupt_member(), _normalize_member_xml(), normalize_pptx_package(), _normalize_shared_strings_xml(), normalize_xlsx_package(), 读取 ZIP 成员；损坏的媒体资源可跳过，关键 XML/关系文件仍保持失败。 (+23 more)

### Community 34 - "Community 34"
Cohesion: 0.13
Nodes (25): append_batch_results_to_middle_json(), _append_formula_number_tag(), append_page_model_infos_to_middle_json(), _apply_post_ocr(), build_page_model_info(), _extract_text_from_block(), finalize_middle_json(), _get_interline_equation_span() (+17 more)

### Community 35 - "Community 35"
Cohesion: 0.13
Nodes (18): _build_sortable_entries(), _calculate_bounding_region(), _calculate_horizontal_overlap_ratio(), _compute_density_ratio(), _CutInfo, _find_best_horizontal_cut_with_projection(), _find_best_vertical_cut_with_projection(), _find_vertical_cut_by_edges() (+10 more)

### Community 36 - "Community 36"
Cohesion: 0.12
Nodes (7): __child_kind(), __copy_block_fields(), __fix_text_block(), __is_inline_formula_block(), __is_ocr_text_block(), MagicModel, __make_child_block()

### Community 37 - "Community 37"
Cohesion: 0.14
Nodes (24): classify(), classify_hybrid(), classify_legacy(), detect_cid_font_signal_pypdf(), detect_invalid_chars(), detect_invalid_chars_pdfminer_fallback(), extract_pages(), extract_selected_pages() (+16 more)

### Community 38 - "Community 38"
Cohesion: 0.13
Nodes (4): _copy_raw_text_block_metadata(), fix_list_blocks(), MagicModel, _split_page_model_list()

### Community 39 - "Community 39"
Cohesion: 0.2
Nodes (17): compare_field(), _handoff_completeness_score(), _iter_jsonl(), _layer_d_failure_recovery_score(), load_expected_map(), _load_json(), main(), _norm_list() (+9 more)

### Community 40 - "Community 40"
Cohesion: 0.2
Nodes (13): annotate_hybrid_cross_page_merge_prev(), _block_has_lines(), _build_bbox_fs(), can_merge_text_blocks(), _find_first_page_edge_text_block(), _find_last_page_edge_text_block(), _find_previous_text_block(), _first_span() (+5 more)

### Community 41 - "Community 41"
Cohesion: 0.12
Nodes (16): bbox_center_distance(), bbox_distance(), bbox_relative_pos(), calculate_iou(), calculate_overlap_area_2_minbox_area_ratio(), calculate_overlap_area_in_bbox1_area_ratio(), calculate_vertical_projection_overlap_ratio(), get_minbox_if_overlap_by_ratio() (+8 more)

### Community 42 - "Community 42"
Cohesion: 0.13
Nodes (3): _copy_raw_text_block_metadata(), fix_list_blocks(), MagicModel

### Community 43 - "Community 43"
Cohesion: 0.17
Nodes (10): get_bucket_name(), get_latex_delimiter_config(), get_llm_aided_config(), get_local_models_dir(), get_s3_config(), get_s3_config_dict(), parse_bucket_key(), ~/magic-pdf.json 读出来. (+2 more)

### Community 44 - "Community 44"
Cohesion: 0.24
Nodes (14): _apply_levels_to_blocks(), _build_title_dict(), _collect_title_block_refs(), _get_title_block_identity(), _get_title_line_avg_height(), llm_aided_title(), _normalize_title_types(), _offset_paragraph_title_levels() (+6 more)

### Community 45 - "Community 45"
Cohesion: 0.19
Nodes (16): calculate_intersection(), clean_memory(), clean_vram(), crop_img(), _get_bbox(), get_coords_and_area(), _get_int_bbox(), get_res_list_from_layout_res() (+8 more)

### Community 46 - "Community 46"
Cohesion: 0.22
Nodes (14): cpu_bar(), cpu_percent(), disk_free_str(), _docker_available(), docker_cpu_percent(), docker_ps_running(), format_system_block(), load_avg_str() (+6 more)

### Community 47 - "Community 47"
Cohesion: 0.21
Nodes (8): BaseImageProcessor, crop_margin(), crop_margin_numpy(), # TODO: dereference cv2 if possible, Calculate padding values for PIL images, Get padding values based on image dimensions and padding strategy, Convert PIL Image or numpy array to properly sized and padded image after:, UnimerSwinImageProcessor

### Community 48 - "Community 48"
Cohesion: 0.23
Nodes (11): absorb_image_block_members(), bbox_area(), child_kind_from_type(), child_visual_type(), clamp_and_round(), code_content_clean(), find_best_visual_parent(), is_visual_neighbor() (+3 more)

### Community 49 - "Community 49"
Cohesion: 0.18
Nodes (10): compute_iou(), deal_bb(), deal_duplicate_bb(), deal_eb_token(), deal_isolate_span(), In our opinion, <b></b> always occurs in <thead></thead> text's context.     Th, post process with <eb></eb>, <eb1></eb1>, ...     emptyBboxTokenDict = {, Deal with isolate span cases in this function.     It causes by wrong predictio (+2 more)

### Community 50 - "Community 50"
Cohesion: 0.2
Nodes (8): AnalysisConfig(), init_args(), parse_args(), resize img and limit the longest side of the image to input_size, Count the number of Chinese characters,     a single English character and a si, read_network_config_from_yaml(), resize_img(), str_count()

### Community 51 - "Community 51"
Cohesion: 0.38
Nodes (9): append_page_model_list_to_middle_json(), append_page_results_to_middle_json(), _apply_post_ocr(), blocks_to_page_info(), _detect_block_line_bboxes(), _detect_edge_text_line_hints(), finalize_middle_json(), init_middle_json() (+1 more)

### Community 52 - "Community 52"
Cohesion: 0.47
Nodes (8): create_text_placeholder(), is_vector_image(), is_vector_image_part(), _load_placeholder_font(), serialize_office_image(), serialize_vector_image_with_placeholder(), serialize_vector_part_with_placeholder(), _vector_image_format_label()

### Community 53 - "Community 53"
Cohesion: 0.42
Nodes (8): calculate_char_in_span(), calculate_contrast(), chars_to_content(), fill_char_in_spans(), _prepare_post_ocr_spans(), __replace_ligatures(), __replace_unicode(), txt_spans_extract()

### Community 54 - "Community 54"
Cohesion: 0.43
Nodes (7): _diff_sets(), _extract_signals_keywords_from_rules_yaml(), main(), Smoke-check `.cursor/rules/always-orchestrator-skill.mdc`.     Requirements:, YAML-lite extractor for:       signals:         <agent_id>:           keyword, _run_self_tests(), _validate_always_orchestrator_rule()

### Community 55 - "Community 55"
Cohesion: 0.48
Nodes (6): _detect_direct_implementation_signatures(), _has_phase2_gate_mention(), _looks_like_implementation_or_mixed(), main(), Catch obvious violations: orchestrator directly outputting a patch/diff/code-edi, validate_trace()

### Community 56 - "Community 56"
Cohesion: 0.48
Nodes (5): build_form_data(), collect_input_files(), main(), prepare_local_api_temp_dir(), run_demo()

### Community 57 - "Community 57"
Cohesion: 0.29
Nodes (6): full_to_half(), full_to_half_exclude_marks(), is_hyphen_at_line_end(), 判断文本行是否以英文单词的跨行断词符结尾。      只识别字母后紧跟行末 hyphen 的断词场景，不处理词内连字符或普通破折号。, Convert full-width characters to half-width characters using code point manipula, Convert full-width characters to half-width characters using code point manipula

### Community 58 - "Community 58"
Cohesion: 0.48
Nodes (6): _format_engine_name(), get_vlm_engine(), 自动选择或验证 VLM 推理引擎      Args:         inference_engine: 指定的引擎名称或 'auto' 进行自动选择, _select_linux_engine(), _select_mac_engine(), _select_windows_engine()

### Community 59 - "Community 59"
Cohesion: 0.48
Nodes (6): fix_text_block(), line_sort_spans_by_left_to_right(), merge_spans_to_line(), merge_spans_to_vertical_line(), 将纵向文本的spans合并成纵向lines（从右向左阅读）, vertical_line_sort_spans_from_top_to_bottom()

### Community 60 - "Community 60"
Cohesion: 0.47
Nodes (4): build_local_api_cli_args(), maybe_preload_vlm_model(), preload_vlm_model(), resolve_gradio_local_api_cli_args()

### Community 61 - "Community 61"
Cohesion: 0.4
Nodes (5): parse_s3_range_params(), parse_s3path(), example: s3://abc/xxxx.json?bytes=0,81350 ==> [0, 81350], example: s3://abc/xxxx.json?bytes=0,81350 ==> s3://abc/xxxx.json, remove_non_official_s3_args()

### Community 62 - "Community 62"
Cohesion: 0.47
Nodes (3): is_apple_silicon_cpu(), is_mac_environment(), is_mac_os_version_supported()

### Community 63 - "Community 63"
Cohesion: 0.67
Nodes (5): close_pdfium_document(), get_pdfium_document_page_count(), open_pdfium_document(), pdfium_guard(), rewrite_pdf_bytes_with_pdfium()

### Community 64 - "Community 64"
Cohesion: 0.53
Nodes (4): assert_content(), run_pipeline_parse(), test_pipeline_with_two_config(), validate_html()

### Community 65 - "Community 65"
Cohesion: 0.4
Nodes (4): escape_conservative_markdown_text(), escape_text_block_markdown_prefix(), Escape plain-text characters that carry inline Markdown semantics., Escape a leading Markdown block marker in an assembled text block.

### Community 66 - "Community 66"
Cohesion: 0.4
Nodes (4): cross_page_table_merge(), exclude_progress_bar_idle_time(), Merge tables that span across multiple pages in a PDF document.      Args:, Exclude non-processing idle time from a reused tqdm progress bar.

### Community 67 - "Community 67"
Cohesion: 0.5
Nodes (2): is_public_bind_host(), warn_if_public_http_client_policy()

### Community 68 - "Community 68"
Cohesion: 0.5
Nodes (4): 从流起点读取完整字节；不可复位的流则从当前位置读取剩余字节。, 将可复位的二进制流移动到起点；不可复位时返回 False。, read_stream_bytes_from_start(), rewind_stream()

### Community 69 - "Community 69"
Cohesion: 0.4
Nodes (2): ClsHead, Class orientation     Args:         params(dict): super parameters for build C

### Community 70 - "Community 70"
Cohesion: 0.6
Nodes (4): arg_parse(), _coerce_cli_value(), parse_unknown_args(), Parse unknown click args into keyword arguments.

### Community 71 - "Community 71"
Cohesion: 0.5
Nodes (2): guess_language_by_text(), _normalize_text_for_language_guess()

### Community 72 - "Community 72"
Cohesion: 0.4
Nodes (0): 

### Community 73 - "Community 73"
Cohesion: 0.4
Nodes (4): 去除重叠的bbox，保留不被其他bbox包含的bbox      Args:         bboxes: 包含bbox信息的字典列表      R, 基于index的类别关联方法，用于将主体对象与客体对象进行关联     客体优先匹配给index最接近的主体，匹配优先级为：     1. index差值（, reduct_overlap(), tie_up_category_by_index()

### Community 74 - "Community 74"
Cohesion: 0.7
Nodes (4): get_load_images_threads(), get_load_images_timeout(), get_op_num_threads(), get_value_from_string()

### Community 75 - "Community 75"
Cohesion: 0.83
Nodes (3): _iter_jsonl(), main(), _validate_case()

### Community 76 - "Community 76"
Cohesion: 0.83
Nodes (3): lmdeploy_server(), openai_server(), vllm_server()

### Community 77 - "Community 77"
Cohesion: 0.67
Nodes (2): image_to_b64str(), image_to_bytes()

### Community 78 - "Community 78"
Cohesion: 0.5
Nodes (3): pdf_end_page_for_cli(), Helpers for building MinerU CLI invocations (keeps UI code smaller)., Return inclusive 0-based end page for `mineru -e`, or None when unlimited.

### Community 79 - "Community 79"
Cohesion: 0.67
Nodes (0): 

### Community 80 - "Community 80"
Cohesion: 1.0
Nodes (2): detect_ocr_boxes_from_padded_crop(), get_ch_lite_ocr_det_model()

### Community 81 - "Community 81"
Cohesion: 1.0
Nodes (2): build_parse_dir(), resolve_parse_dir()

### Community 82 - "Community 82"
Cohesion: 1.0
Nodes (2): parse_xml_str(), read_str()

### Community 83 - "Community 83"
Cohesion: 1.0
Nodes (2): detect_lang(), remove_invalid_surrogates()

### Community 84 - "Community 84"
Cohesion: 1.0
Nodes (2): _expand(), main()

### Community 85 - "Community 85"
Cohesion: 1.0
Nodes (0): 

### Community 86 - "Community 86"
Cohesion: 1.0
Nodes (0): 

### Community 87 - "Community 87"
Cohesion: 1.0
Nodes (0): 

### Community 88 - "Community 88"
Cohesion: 1.0
Nodes (0): 

### Community 89 - "Community 89"
Cohesion: 1.0
Nodes (0): 

### Community 90 - "Community 90"
Cohesion: 1.0
Nodes (0): 

### Community 91 - "Community 91"
Cohesion: 1.0
Nodes (0): 

### Community 92 - "Community 92"
Cohesion: 1.0
Nodes (0): 

### Community 93 - "Community 93"
Cohesion: 1.0
Nodes (0): 

### Community 94 - "Community 94"
Cohesion: 1.0
Nodes (0): 

### Community 95 - "Community 95"
Cohesion: 1.0
Nodes (0): 

### Community 96 - "Community 96"
Cohesion: 1.0
Nodes (0): 

### Community 97 - "Community 97"
Cohesion: 1.0
Nodes (1): Read the file at offset and limit.          Args:             path (str): the

### Community 98 - "Community 98"
Cohesion: 1.0
Nodes (1): Write file with data.          Args:             path (str): the path of file

### Community 99 - "Community 99"
Cohesion: 1.0
Nodes (1): Read the file.          Args:             path (str): file path to read

### Community 100 - "Community 100"
Cohesion: 1.0
Nodes (1): Read at offset and limit.          Args:             path (str): the path of

### Community 101 - "Community 101"
Cohesion: 1.0
Nodes (1): Retrieves all special tokens.          Returns:             List[str]: List o

### Community 102 - "Community 102"
Cohesion: 1.0
Nodes (1): Retrieves all special tokens, including extended ones.          Returns:

### Community 103 - "Community 103"
Cohesion: 1.0
Nodes (1): Retrieves the extended map of special tokens.          Returns:             D

### Community 104 - "Community 104"
Cohesion: 1.0
Nodes (1): r"""         labels (`torch.LongTensor` of shape `(batch_size, sequence_length)

### Community 105 - "Community 105"
Cohesion: 1.0
Nodes (1): Crop margins of image using NumPy operations

### Community 106 - "Community 106"
Cohesion: 1.0
Nodes (1): Generate sequences using the UniMERNetHead for inference tasks.          Args:

### Community 107 - "Community 107"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **295 isolated node(s):** `Smoke-check `.cursor/rules/always-orchestrator-skill.mdc`.     Requirements:`, `YAML-lite extractor for:       signals:         <agent_id>:           keyword`, `Load all cases from cases_dir/*.jsonl.     Returns a flat list of dict objects`, `Deterministic task-type classifier (Layer A).      Returns one of:       docs`, `Deterministic gate prediction.      Requirements:     - IMPLEMENTATION or MIX` (+290 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 85`** (2 nodes): `run_all.ps1`, `Resolve-RepoRoot()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 86`** (2 nodes): `docx_analyze.py`, `office_docx_analyze()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 87`** (2 nodes): `pptx_analyze.py`, `office_pptx_analyze()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 88`** (2 nodes): `xlsx_analyze.py`, `office_xlsx_analyze()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 89`** (2 nodes): `lmdeploy_server.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 90`** (2 nodes): `vllm_server.py`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 91`** (2 nodes): `pdf_page_id.py`, `get_end_page_id()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 92`** (2 nodes): `pdf_text_tool.py`, `get_page()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 93`** (2 nodes): `clean_coverage.py`, `delete_file()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 94`** (2 nodes): `get_coverage.py`, `get_covrage()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 95`** (1 nodes): `version.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 96`** (1 nodes): `api_protocol.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 97`** (1 nodes): `Read the file at offset and limit.          Args:             path (str): the`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 98`** (1 nodes): `Write file with data.          Args:             path (str): the path of file`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 99`** (1 nodes): `Read the file.          Args:             path (str): file path to read`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 100`** (1 nodes): `Read at offset and limit.          Args:             path (str): the path of`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 101`** (1 nodes): `Retrieves all special tokens.          Returns:             List[str]: List o`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 102`** (1 nodes): `Retrieves all special tokens, including extended ones.          Returns:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 103`** (1 nodes): `Retrieves the extended map of special tokens.          Returns:             D`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 104`** (1 nodes): `r"""         labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 105`** (1 nodes): `Crop margins of image using NumPy operations`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 106`** (1 nodes): `Generate sequences using the UniMERNetHead for inference tasks.          Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 107`** (1 nodes): `run-mineru-tui.ps1`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ModelPath` connect `Community 1` to `Community 8`, `Community 9`?**
  _High betweenness centrality (0.194) - this node is a cross-community bridge._
- **Why does `HybridDependencyError` connect `Community 5` to `Community 2`, `Community 10`, `Community 14`?**
  _High betweenness centrality (0.190) - this node is a cross-community bridge._
- **Why does `MakeMode` connect `Community 10` to `Community 8`, `Community 2`, `Community 5`?**
  _High betweenness centrality (0.184) - this node is a cross-community bridge._
- **Are the 168 inferred relationships involving `BlockType` (e.g. with `MagicModel` and `Try to extract a leading section number (e.g. '1.2.1') from title content.`) actually correct?**
  _`BlockType` has 168 INFERRED edges - model-reasoned connections that need verification._
- **Are the 107 inferred relationships involving `oMath2Latex` (e.g. with `DocxConverter` and `转义超链接文本中的方括号。          Args:             text: 要转义的文本          Returns:`) actually correct?**
  _`oMath2Latex` has 107 INFERRED edges - model-reasoned connections that need verification._
- **Are the 99 inferred relationships involving `ContentType` (e.g. with `MagicModel` and `MagicModel`) actually correct?**
  _`ContentType` has 99 INFERRED edges - model-reasoned connections that need verification._
- **Are the 59 inferred relationships involving `Script` (e.g. with `DocxConverter` and `转义超链接文本中的方括号。          Args:             text: 要转义的文本          Returns:`) actually correct?**
  _`Script` has 59 INFERRED edges - model-reasoned connections that need verification._