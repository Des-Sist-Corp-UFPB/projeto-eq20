package br.ufpb.dsc.ocorrencias.repository;

import br.ufpb.dsc.ocorrencias.model.Ocorrencia;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface OcorrenciaRepository extends JpaRepository<Ocorrencia, Long> {
}