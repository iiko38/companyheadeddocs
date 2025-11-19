const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://jake-15432--companyheadeddocs-serve.modal.run'

export interface TransformRequest {
  template_id: string
  project: string
  job_min_no: string
  description: string
  date: string
  time: string
  location: string
  file: File
}

export interface TransformResponse {
  request_id: string
  minutes: any // MeetingModel data
  docx_base64: string
}

export class ApiClient {
  private async request(endpoint: string, options: RequestInit = {}): Promise<any> {
    const url = `${API_BASE_URL}${endpoint}`

    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
      },
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`API Error: ${response.status} - ${errorText}`)
    }

    return response.json()
  }

  async transform(data: TransformRequest): Promise<TransformResponse> {
    const formData = new FormData()

    // Add all text fields
    formData.append('template_id', data.template_id)
    formData.append('project', data.project)
    formData.append('job_min_no', data.job_min_no)
    formData.append('description', data.description)
    formData.append('date', data.date)
    formData.append('time', data.time)
    formData.append('location', data.location)

    // Add file
    formData.append('file', data.file)

    console.log('Starting transcript processing...')

    const response = await fetch(`${API_BASE_URL}/transform`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Transform request failed:', errorText)
      throw new Error(`Transform failed: ${response.status} - ${errorText}`)
    }

    const result = await response.json()
    console.log('Transform completed successfully')
    return result
  }

  async health(): Promise<{ status: string }> {
    return this.request('/health')
  }
}

export const apiClient = new ApiClient()
