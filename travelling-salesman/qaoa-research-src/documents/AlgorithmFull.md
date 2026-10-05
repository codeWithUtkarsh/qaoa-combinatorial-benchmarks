# Metadata Calculation Flow in SamplingVQE

## Main Metadata Flow Diagram

```mermaid
flowchart TD
    A[evaluate_energy called] --> B[Parameters reshaped to batch]
    B --> C[estimator.run called]
    
    subgraph "DiagonalEstimator.run()"
        C --> D[Create AlgorithmJob]
        D --> E[job.submit]
        E --> F[_call method executed]
    end
    
    subgraph "_DiagonalEstimator._call()"
        F --> G[sampler.run called]
        G --> H[Sampler Job Execution]
        H --> I[sampler_job.result]
        I --> J[sampler_result obtained]
        J --> K[Extract sampler_result.metadata]
        K --> L[Process measurements]
        L --> M[Return _DiagonalEstimatorResult]
    end
    
    M --> N[estimator_result = job.result]
    N --> O[metadata = estimator_result.metadata]
    O --> P[Callback with metadata]
    
    style O fill:#ff9999,stroke:#333,stroke-width:4px
    style K fill:#ffcc99,stroke:#333,stroke-width:2px
    style J fill:#99ccff,stroke:#333,stroke-width:2px
```

## Detailed Metadata Generation Process

```mermaid
sequenceDiagram
    participant EE as evaluate_energy
    participant DE as DiagonalEstimator
    participant AJ as AlgorithmJob
    participant S as Sampler
    participant B as Backend/Simulator
    participant DR as _DiagonalEstimatorResult
    
    Note over EE: metadata = estimator_result.metadata
    
    EE->>DE: estimator.run(circuits, operators, params)
    DE->>AJ: Create AlgorithmJob(_call, ...)
    AJ->>AJ: job.submit()
    
    Note over AJ: _call method execution begins
    
    AJ->>S: sampler.run(circuits, parameter_values)
    S->>B: Execute quantum circuits
    
    Note over B: Backend generates execution metadata:<br/>- shots, duration, errors<br/>- calibration data, noise info<br/>- job statistics
    
    B-->>S: Raw execution results + metadata
    S->>S: Process into SamplerResult
    
    Note over S: SamplerResult contains:<br/>- quasi_dists<br/>- metadata (from backend)
    
    S-->>AJ: sampler_result with metadata
    AJ->>AJ: Process measurement data
    AJ->>DR: Create _DiagonalEstimatorResult
    
    Note over DR: Pass through sampler metadata:<br/>metadata=sampler_result.metadata
    
    DR-->>DE: Return estimator_result
    DE-->>EE: estimator_result with metadata
    
    Note over EE: Extract: metadata = estimator_result.metadata
    
    EE->>EE: Use metadata in callback
```

## Metadata Content Structure

```mermaid
graph TB
    subgraph "Backend Level"
        A1[Hardware Calibration]
        A2[Execution Statistics]
        A3[Error Information]
        A4[Timing Data]
    end
    
    subgraph "Sampler Level"
        B1[Shot Count]
        B2[Circuit Compilation]
        B3[Job Management]
        B4[Measurement Processing]
    end
    
    subgraph "DiagonalEstimator Level"
        C1[Aggregation Method]
        C2[Best Measurements]
        C3[Processing Stats]
    end
    
    subgraph "Final Metadata"
        D1[Combined Execution Info]
        D2[Performance Metrics]
        D3[Quality Indicators]
    end
    
    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> B4
    
    B1 --> C1
    B2 --> C2
    B3 --> C3
    B4 --> C1
    
    C1 --> D1
    C2 --> D2
    C3 --> D3
```

## Code Trace: Metadata Calculation Points

```mermaid
flowchart LR
    subgraph "1. Sampler Execution"
        A["`sampler.run()
        Creates job with circuits`"]
        B["`Backend executes
        Generates metadata`"]
        C["`sampler_result.metadata
        Contains execution info`"]
    end
    
    subgraph "2. DiagonalEstimator Processing"
        D["`_call method
        Gets sampler_result`"]
        E["`Extract metadata:
        sampler_result.metadata`"]
        F["`Pass to result:
        metadata=metadata`"]
    end
    
    subgraph "3. Algorithm Level"
        G["`estimator_result
        Contains metadata`"]
        H["`Line: metadata = 
        estimator_result.metadata`"]
        I["`Callback receives
        metadata`"]
    end
    
    A --> B --> C
    C --> D --> E --> F
    F --> G --> H --> I
    
    style H fill:#ff6666,stroke:#333,stroke-width:3px
```

## Metadata Types by Backend

```mermaid
graph TD
    subgraph "Simulator Backends"
        S1["`**Statevector Simulator**
        - shots: None
        - method: 'statevector'
        - precision: 'double'
        - memory_usage: X MB`"]
        
        S2["`**QASM Simulator**
        - shots: 1024
        - method: 'qasm'
        - noise_model: {...}
        - seed: 42`"]
    end
    
    subgraph "Hardware Backends"
        H1["`**IBM Quantum**
        - shots: 1000
        - job_id: 'abc123'
        - backend_name: 'ibm_brisbane'
        - calibration_date: '2024-01-01'
        - gate_errors: {...}
        - readout_errors: {...}`"]
    end
    
    subgraph "Custom Samplers"
        C1["`**Custom Implementation**
        - implementation_specific
        - performance_metrics
        - custom_statistics`"]
    end
    
    A[Metadata Source] --> S1
    A --> S2
    A --> H1
    A --> C1
```

## Metadata Processing in _DiagonalEstimator

```mermaid
flowchart TD
    A[sampler_job.result] --> B[sampler_result obtained]
    
    B --> C{Process samples}
    C --> D[Calculate expectation values]
    C --> E[Track best measurements]
    
    D --> F[Create results array]
    E --> G[Update best_measurements]
    
    F --> H["`_DiagonalEstimatorResult(
        values=results,
        metadata=sampler_result.metadata,  ← PASSTHROUGH
        best_measurements=best_measurements
    )`"]
    
    G --> H
    
    style H fill:#99ff99,stroke:#333,stroke-width:2px
    
    subgraph "Key Point"
        I["`Metadata is PASSED THROUGH
        from sampler to estimator result
        WITHOUT modification`"]
    end
```

## Example Metadata Flow

```mermaid
flowchart LR
    subgraph "Step 1: Backend Execution"
        A1["`Backend generates:
        {
          'shots': 1000,
          'duration': 0.15,
          'job_id': 'job_123'
        }`"]
    end
    
    subgraph "Step 2: Sampler Result"
        B1["`SamplerResult:
        - quasi_dists: [...]
        - metadata: [backend_meta]`"]
    end
    
    subgraph "Step 3: DiagonalEstimator"
        C1["`_DiagonalEstimatorResult:
        - values: [...]
        - metadata: sampler_meta  ← SAME
        - best_measurements: [...]`"]
    end
    
    subgraph "Step 4: evaluate_energy"
        D1["`estimator_result.metadata
        = sampler_result.metadata
        = backend metadata`"]
    end
    
    A1 --> B1 --> C1 --> D1
    
    style D1 fill:#ff9999,stroke:#333,stroke-width:3px
```

## Key Insights

1. **Passthrough Nature**: Metadata flows through without modification from backend → sampler → estimator → algorithm
2. **Backend Origin**: The actual metadata content is generated at the backend/hardware level
3. **Per-Circuit**: Each circuit execution gets its own metadata entry
4. **Rich Information**: Contains execution context, performance metrics, and quality indicators
5. **Debug Value**: Essential for monitoring algorithm performance and troubleshooting issues