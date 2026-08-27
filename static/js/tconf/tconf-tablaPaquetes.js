$(document).ready(function() {
    $('#tablaPaquetes').DataTable({
         order: [],
       // 1. ESTRUCTURA VISUAL: Mantiene botones y buscador alineados en la misma fila
        dom: "<'row mb-3 align-items-center'<'col-md-6'B><'col-md-6 d-flex justify-content-end'f>>" +
             "<'row'<'col-sm-12'tr>>" +
             "<'row mt-3'<'col-md-5'i><'col-md-7 d-flex justify-content-end'p>>",

      
// 2. BOTONES DE EXPORTACIÓN CON LOGOS OFICIALES (COMO LA IMAGEN)

  buttons: [
    {
        extend: 'excelHtml5',
        text: '<i class="bi bi-file-earmark-excel-fill text-success fs-5"></i>',
        titleAttr: 'Exportar a Excel',
        className: 'btn btn-light rounded-circle shadow-sm border-0 mx-1 d-flex align-items-center justify-content-center p-0',
        attr: {
            style: 'width:48px;height:48px;flex-shrink: 0;'
        }
    },
    {
        extend: 'pdfHtml5',
        text: '<i class="bi bi-file-earmark-pdf-fill text-dark fs-5"></i>',
        titleAttr: 'Exportar a PDF',
        className: 'btn btn-light rounded-circle shadow-sm border-0 mx-1 d-flex align-items-center justify-content-center p-0',
        attr: {
            style: 'width:48px;height:48px; flex-shrink: 0;'
        }
    },
    {
        extend: 'print',
        text: '<i class="bi bi-printer-fill text-dark fs-5"></i>',
        titleAttr: 'Imprimir',
        className: 'btn btn-light rounded-circle shadow-sm border-0 mx-1 d-flex align-items-center justify-content-center p-0',
        attr: {
            style: 'width:48px;height:48px; flex-shrink: 0;'
        }
    }
],
        // 3. TRADUCCIÓN COMPLETA DE TU PROYECTO MONAGUA
        language: {
            sProcessing:     "Procesando...",
            sLengthMenu:     "Mostrar _MENU_ registros",
            sZeroRecords:    "No se encontraron resultados",
            sEmptyTable:     "Ningún dato disponible en esta tabla",
            sInfo:           "Mostrando registros del _START_ al _END_ de un total de _TOTAL_ registros",
            sInfoEmpty:      "Mostrando registros del 0 al 0 de un total de 0 registros",
            sInfoFiltered:   "(filtrado de un total de _MAX_ registros)",
            sInfoPostFix:    "",
            sSearch:         "Buscar:",
            sUrl:            "",
            sInfoThousands:  ",",
            sLoadingRecords: "Cargando...",
            oPaginate: {
                sFirst:    "Primero",
                sLast:     "Último",
                sNext:     "Siguiente",
                sPrevious: "Anterior"
            },
            oAria: {
                sSortAscending:  ": Activar para ordenar la columna de manera ascendente",
                sSortDescending: ": Activar para ordenar la columna de manera descendente"
            }
        },

        // 4. CONFIGURACIÓN DE AJUSTES Y RESPONSIVE
        responsive: false,
        autoWidth: true,
        scrollX: false,
        scrollCollapse: false
    });
});