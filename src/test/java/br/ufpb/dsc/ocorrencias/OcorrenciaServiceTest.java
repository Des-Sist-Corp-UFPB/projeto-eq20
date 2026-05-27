import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import br.ufpb.dsc.ocorrencias.model.Ocorrencia;
import br.ufpb.dsc.ocorrencias.repository.OcorrenciaRepository;
import br.ufpb.dsc.ocorrencias.service.OcorrenciaService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.util.Optional;

class OcorrenciaServiceTest {

    @InjectMocks
    private OcorrenciaService ocorrenciaService;

    @Mock
    private OcorrenciaRepository ocorrenciaRepository;

    private Ocorrencia ocorrencia;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        ocorrencia = new Ocorrencia();
        ocorrencia.setId(1L);
        ocorrencia.setType("Pothole");
        ocorrencia.setDescription("Large pothole on Main St.");
        ocorrencia.setLocation("Main St.");
        ocorrencia.setStatus("Open");
    }

    @Test
    void testCreateOcorrencia() {
        when(ocorrenciaRepository.save(any(Ocorrencia.class))).thenReturn(ocorrencia);
        Ocorrencia created = ocorrenciaService.createOcorrencia(ocorrencia);
        assertNotNull(created);
        assertEquals(1L, created.getId());
    }

    @Test
    void testGetOcorrenciaById() {
        when(ocorrenciaRepository.findById(1L)).thenReturn(Optional.of(ocorrencia));
        Optional<Ocorrencia> found = ocorrenciaService.getOcorrenciaById(1L);
        assertTrue(found.isPresent());
        assertEquals("Pothole", found.get().getType());
    }

    @Test
    void testUpdateOcorrencia() {
        when(ocorrenciaRepository.findById(1L)).thenReturn(Optional.of(ocorrencia));
        ocorrencia.setDescription("Updated description");
        when(ocorrenciaRepository.save(any(Ocorrencia.class))).thenReturn(ocorrencia);
        Ocorrencia updated = ocorrenciaService.updateOcorrencia(1L, ocorrencia);
        assertEquals("Updated description", updated.getDescription());
    }

    @Test
    void testDeleteOcorrencia() {
        doNothing().when(ocorrenciaRepository).deleteById(1L);
        ocorrenciaService.deleteOcorrencia(1L);
        verify(ocorrenciaRepository, times(1)).deleteById(1L);
    }
}