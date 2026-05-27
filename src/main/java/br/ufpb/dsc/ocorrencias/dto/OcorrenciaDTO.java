package br.ufpb.dsc.ocorrencias.dto;

public record OcorrenciaDTO(
    Long id,
    String tipo,
    String descricao,
    String localizacao,
    String status
) {}