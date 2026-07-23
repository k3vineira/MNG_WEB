$(document).ready(function () {
    $('#tablaCancelaciones').DataTable({
         order: [],
        // CONFIGURACIÓN CLAVE: Colocamos botones (B) y buscador (f) en la misma línea
        dom: "<'row mb-3 align-items-center'<'col-md-6'B><'col-md-6 d-flex justify-content-end'f>>" +
             "<'row'<'col-sm-12'tr>>" +
             "<'row mt-3'<'col-md-5'i><'col-md-7 d-flex justify-content-end'p>>",

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

        language: {
            sSearch: "Buscar:",
            sLengthMenu: "Mostrar _MENU_ registros",
            sInfo: "Mostrando _START_ a _END_ de _TOTAL_ registros",
            sZeroRecords: "No se encontraron resultados",
            sEmptyTable: "No hay datos disponibles"
        },

        responsive: false,
        autoWidth: true,
        scrollX: false,
        scrollCollapse: false
    });
});