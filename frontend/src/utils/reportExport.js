const INVALID_FILENAME_RE = /[\\/:*?"<>|\s]+/g

const sanitizeFileSegment = (value, fallback) => {
  const normalized = String(value || '')
    .trim()
    .replace(INVALID_FILENAME_RE, '_')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '')

  return normalized || fallback
}

export const buildReportPdfFilename = (username, trainingType, trainingId) => {
  const safeUsername = sanitizeFileSegment(username, '用户')
  const safeTrainingType = sanitizeFileSegment(trainingType, '训练报告')
  const safeTrainingId = sanitizeFileSegment(trainingId, '未知ID')
  return `${safeUsername}_${safeTrainingType}_${safeTrainingId}.pdf`
}

export const exportElementToPdf = async ({
  element,
  filename,
  margin = 10,
  a4ContentWidthPx = 1040
}) => {
  if (!element) {
    throw new Error('未找到可导出的报告内容')
  }

  const [{ default: html2canvas }, { jsPDF }] = await Promise.all([
    import('html2canvas'),
    import('jspdf')
  ])

  const exportRoot = document.createElement('div')
  exportRoot.style.position = 'fixed'
  exportRoot.style.left = '-10000px'
  exportRoot.style.top = '0'
  exportRoot.style.width = `${a4ContentWidthPx}px`
  exportRoot.style.padding = '0'
  exportRoot.style.margin = '0'
  exportRoot.style.background = '#ffffff'
  exportRoot.style.zIndex = '-1'
  exportRoot.style.pointerEvents = 'none'

  const clonedElement = element.cloneNode(true)
  clonedElement.style.width = '100%'
  clonedElement.style.maxWidth = '100%'
  clonedElement.style.margin = '0'
  clonedElement.style.boxSizing = 'border-box'

  exportRoot.appendChild(clonedElement)
  document.body.appendChild(exportRoot)

  try {
    const canvas = await html2canvas(exportRoot, {
      scale: Math.max(window.devicePixelRatio || 1, 2),
      useCORS: true,
      backgroundColor: '#ffffff',
      scrollX: 0,
      scrollY: 0,
      windowWidth: a4ContentWidthPx,
      width: exportRoot.scrollWidth,
      height: exportRoot.scrollHeight
    })

    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const renderWidth = pageWidth - margin * 2
    const renderHeight = pageHeight - margin * 2

    const pageCanvasHeight = Math.floor((renderHeight / renderWidth) * canvas.width)
    let renderedHeight = 0
    let pageIndex = 0

    while (renderedHeight < canvas.height) {
      const currentSliceHeight = Math.min(pageCanvasHeight, canvas.height - renderedHeight)
      const pageCanvas = document.createElement('canvas')
      pageCanvas.width = canvas.width
      pageCanvas.height = currentSliceHeight

      const pageContext = pageCanvas.getContext('2d')
      if (!pageContext) {
        throw new Error('无法创建 PDF 页面画布')
      }

      pageContext.fillStyle = '#ffffff'
      pageContext.fillRect(0, 0, pageCanvas.width, pageCanvas.height)
      pageContext.drawImage(
        canvas,
        0,
        renderedHeight,
        canvas.width,
        currentSliceHeight,
        0,
        0,
        canvas.width,
        currentSliceHeight
      )

      const pageImgData = pageCanvas.toDataURL('image/jpeg', 0.95)
      const currentRenderHeight = (currentSliceHeight * renderWidth) / canvas.width

      if (pageIndex > 0) {
        pdf.addPage()
      }
      pdf.addImage(pageImgData, 'JPEG', margin, margin, renderWidth, currentRenderHeight)

      renderedHeight += currentSliceHeight
      pageIndex += 1
    }

    pdf.save(filename)
  } finally {
    document.body.removeChild(exportRoot)
  }
}
