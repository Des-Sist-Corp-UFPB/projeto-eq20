package br.ufpb.dsc.ocorrencias.service;

import br.ufpb.dsc.ocorrencias.dto.OcorrenciaDTO;
import br.ufpb.dsc.ocorrencias.model.Ocorrencia;
import br.ufpb.dsc.ocorrencias.repository.OcorrenciaRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
@Transactional
public class OcorrenciaService {

    private final OcorrenciaRepository ocorrenciaRepository;

    @Autowired
    public OcorrenciaService(OcorrenciaRepository ocorrenciaRepository) {
        this.ocorrenciaRepository = ocorrenciaRepository;
    }

    public List<Ocorrencia> findAll() {
        return ocorrenciaRepository.findAll();
    }

    public Optional<Ocorrencia> findById(Long id) {
        return ocorrenciaRepository.findById(id);
    }

    public Ocorrencia create(OcorrenciaDTO ocorrenciaDTO) {
        Ocorrencia ocorrencia = new Ocorrencia(ocorrenciaDTO);
        return ocorrenciaRepository.save(ocorrencia);
    }

    public Ocorrencia update(Long id, OcorrenciaDTO ocorrenciaDTO) {
        Ocorrencia ocorrencia = ocorrenciaRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Ocorrência não encontrada"));
        ocorrencia.updateFromDTO(ocorrenciaDTO);
        return ocorrenciaRepository.save(ocorrencia);
    }

    public void delete(Long id) {
        ocorrenciaRepository.deleteById(id);
    }
}