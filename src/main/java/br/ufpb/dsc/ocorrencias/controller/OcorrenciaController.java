package br.ufpb.dsc.ocorrencias.controller;

import br.ufpb.dsc.ocorrencias.dto.OcorrenciaDTO;
import br.ufpb.dsc.ocorrencias.service.OcorrenciaService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/ocorrencias")
public class OcorrenciaController {

    private final OcorrenciaService ocorrenciaService;

    public OcorrenciaController(OcorrenciaService ocorrenciaService) {
        this.ocorrenciaService = ocorrenciaService;
    }

    @PostMapping
    public ResponseEntity<OcorrenciaDTO> createOcorrencia(@RequestBody OcorrenciaDTO ocorrenciaDTO) {
        OcorrenciaDTO createdOcorrencia = ocorrenciaService.createOcorrencia(ocorrenciaDTO);
        return ResponseEntity.status(201).body(createdOcorrencia);
    }

    @GetMapping("/{id}")
    public ResponseEntity<OcorrenciaDTO> getOcorrencia(@PathVariable Long id) {
        OcorrenciaDTO ocorrenciaDTO = ocorrenciaService.getOcorrenciaById(id);
        return ResponseEntity.ok(ocorrenciaDTO);
    }

    @GetMapping
    public ResponseEntity<List<OcorrenciaDTO>> getAllOcorrencias() {
        List<OcorrenciaDTO> ocorrencias = ocorrenciaService.getAllOcorrencias();
        return ResponseEntity.ok(ocorrencias);
    }

    @PutMapping("/{id}")
    public ResponseEntity<OcorrenciaDTO> updateOcorrencia(@PathVariable Long id, @RequestBody OcorrenciaDTO ocorrenciaDTO) {
        OcorrenciaDTO updatedOcorrencia = ocorrenciaService.updateOcorrencia(id, ocorrenciaDTO);
        return ResponseEntity.ok(updatedOcorrencia);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteOcorrencia(@PathVariable Long id) {
        ocorrenciaService.deleteOcorrencia(id);
        return ResponseEntity.noContent().build();
    }
}